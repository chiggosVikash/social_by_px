import logging
from typing import List, Any, Optional

from llama_index.core import Settings, Document, VectorStoreIndex, StorageContext, QueryBundle
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from core.config import get_settings

logger = logging.getLogger(__name__)

# [DRY] Extract repeated collection names
TEMPLATE_COLLECTION = "template_index"
CREATOR_COLLECTION = "creator_index"


class RAGService:
    # [SOLID: DIP] Receive dependencies rather than creating them
    def __init__(self, client: Optional[QdrantClient]):
        self.client = client
        self.settings = get_settings()

    def seed_initial_templates(self):
        """Seed Qdrant with narrative blueprints and templates."""
        if not self.client:
            return
            
        templates = [
            Document(
                text="A successful carousel starts with a strong hook posing a contrarian question, followed by 3 slides of data-backed insights, and ends with a clear call-to-action.",
                metadata={"type": "carousel_structure", "theme": "educational"}
            ),
            Document(
                text="For thought-leadership posts, frame the narrative around a personal failure or lesson learned, detailing the steps to overcome it.",
                metadata={"type": "narrative_arc", "theme": "personal_story"}
            )
        ]
        
        try:
            # enable_hybrid=True configures FastEmbed sparse vectors (BM25/SPLADE) alongside Gemini dense vectors
            vector_store = QdrantVectorStore(client=self.client, collection_name=TEMPLATE_COLLECTION, enable_hybrid=True)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            VectorStoreIndex.from_documents(
                templates, storage_context=storage_context
            )
            logger.info("Successfully seeded initial templates into Qdrant.")
        except Exception as e:
            logger.error(f"Failed to seed templates: {e}")

    def retrieve_context(self, creator_id: int, keywords: List[str], industry: str) -> str:
        """
        Pull templates, domain knowledge, and creator writing style.
        Uses Hybrid Search (Vector + Sparse) and Cohere Reranking.
        """
        if not self.client:
            return "Fallback context: Create professional, engaging content based on the provided keywords."

        query = f"Industry: {industry}. Keywords: {', '.join(keywords)}"
        context_parts = []
        
        reranker = None
        if self.settings.COHERE_API_KEY:
            try:
                from llama_index.postprocessor.cohere_rerank import CohereRerank
                reranker = CohereRerank(api_key=self.settings.COHERE_API_KEY, top_n=3)
            except ImportError:
                logger.warning("CohereRerank not available. Please install llama-index-postprocessor-cohere-rerank.")
        
        query_bundle = QueryBundle(query)

        try:
            # 1. Retrieve structural templates using Hybrid Search
            template_store = QdrantVectorStore(client=self.client, collection_name=TEMPLATE_COLLECTION, enable_hybrid=True)
            template_index = VectorStoreIndex.from_vector_store(template_store)
            # Fetch top 10 from hybrid search
            template_retriever = template_index.as_retriever(similarity_top_k=10)
            template_nodes = template_retriever.retrieve(query)
            
            # Rerank to top 3
            if reranker and template_nodes:
                template_nodes = reranker.postprocess_nodes(template_nodes, query_bundle)
            elif template_nodes:
                template_nodes = template_nodes[:3]

            if template_nodes:
                context_parts.append("### Content Templates & Structures")
                for node in template_nodes:
                    context_parts.append(f"- {node.text}")

            # 2. Retrieve Creator History (isolated by metadata)
            creator_store = QdrantVectorStore(client=self.client, collection_name=CREATOR_COLLECTION, enable_hybrid=True)
            creator_index = VectorStoreIndex.from_vector_store(creator_store)
            
            from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="creator_id", value=creator_id)]
            )
            
            # Fetch top 10 from hybrid search
            creator_retriever = creator_index.as_retriever(similarity_top_k=10, filters=filters)
            creator_nodes = creator_retriever.retrieve(query)
            
            # Rerank to top 3
            if reranker and creator_nodes:
                creator_nodes = reranker.postprocess_nodes(creator_nodes, query_bundle)
            elif creator_nodes:
                creator_nodes = creator_nodes[:3]
            
            if creator_nodes:
                context_parts.append("\n### Creator Writing Style & Past Successes")
                for node in creator_nodes:
                    context_parts.append(f"- {node.text}")
                    
        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}")
            return "Fallback context: Create professional, engaging content."

        return "\n".join(context_parts)

    def ingest_approved_slides(self, creator_id: int, slides: List[Any], article_title: str) -> None:
        """
        Insert approved slides into Qdrant with `creator_id` metadata using Hybrid indexing.
        """
        if not self.client:
            return

        documents = []
        for slide in slides:
            content = f"Hook: {slide.hook_type}\nText: {slide.text_content}\nCaption: {slide.caption}"
            doc = Document(
                text=content,
                metadata={
                    "creator_id": creator_id,
                    "article_title": article_title,
                    "slide_id": slide.id,
                    "visual_type": slide.visual_type
                }
            )
            documents.append(doc)

        try:
            vector_store = QdrantVectorStore(client=self.client, collection_name=CREATOR_COLLECTION, enable_hybrid=True)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            VectorStoreIndex.from_documents(
                documents, storage_context=storage_context
            )
            logger.info(f"Successfully ingested {len(documents)} approved slides for creator {creator_id}.")
        except Exception as e:
            logger.error(f"Failed to ingest approved slides for creator {creator_id}: {e}")

# [SOLID: SRP] Extract initialization logic into a factory
_rag_service_instance: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service_instance
    if _rag_service_instance is not None:
        return _rag_service_instance

    settings = get_settings()
    
    if settings.GEMINI_API_KEY:
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name="models/gemini-embedding-001",
            api_key=settings.GEMINI_API_KEY
        )
    else:
        logger.warning("GEMINI_API_KEY not set. RAG capabilities will fail if invoked.")

    client = None
    try:
        if settings.QDRANT_URL and settings.QDRANT_API_KEY:
            client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        else:
            logger.warning("No Qdrant credentials found. Falling back to in-memory Qdrant.")
            client = QdrantClient(":memory:")

        # We defer collection creation to QdrantVectorStore so it can properly set up
        # the sparse vector configuration (enable_hybrid=True) automatically.

    except Exception as e:
        logger.error(f"Failed to setup Qdrant client: {e}")

    _rag_service_instance = RAGService(client=client)
    return _rag_service_instance
