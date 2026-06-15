import logging
from typing import List, Any, Optional

from llama_index.core import Settings, Document, VectorStoreIndex, StorageContext
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from core.config import get_settings

logger = logging.getLogger(__name__)

# [DRY] Extract repeated collection names
TEMPLATE_COLLECTION = "template_index"
CREATOR_COLLECTION = "creator_index"


class RAGService:
    # [SOLID: DIP] Receive dependencies rather than creating them
    def __init__(self, client: Optional[QdrantClient]):
        self.client = client

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
            vector_store = QdrantVectorStore(client=self.client, collection_name=TEMPLATE_COLLECTION)
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
        Uses metadata filtering to isolate the creator's history.
        """
        if not self.client:
            return "Fallback context: Create professional, engaging content based on the provided keywords."

        query = f"Industry: {industry}. Keywords: {', '.join(keywords)}"
        context_parts = []
        
        try:
            # 1. Retrieve structural templates
            template_store = QdrantVectorStore(client=self.client, collection_name=TEMPLATE_COLLECTION)
            template_index = VectorStoreIndex.from_vector_store(template_store)
            template_retriever = template_index.as_retriever(similarity_top_k=2)
            template_nodes = template_retriever.retrieve(query)
            if template_nodes:
                context_parts.append("### Content Templates & Structures")
                for node in template_nodes:
                    context_parts.append(f"- {node.text}")

            # 2. Retrieve Creator History (isolated by metadata)
            creator_store = QdrantVectorStore(client=self.client, collection_name=CREATOR_COLLECTION)
            creator_index = VectorStoreIndex.from_vector_store(creator_store)
            
            from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="creator_id", value=creator_id)]
            )
            
            creator_retriever = creator_index.as_retriever(similarity_top_k=3, filters=filters)
            creator_nodes = creator_retriever.retrieve(query)
            
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
        Insert approved slides into Qdrant with `creator_id` metadata.
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
            vector_store = QdrantVectorStore(client=self.client, collection_name=CREATOR_COLLECTION)
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
            model_name="models/text-embedding-004",
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

        # [YAGNI] Removed speculative domain_index
        collections = [TEMPLATE_COLLECTION, CREATOR_COLLECTION]
        for col in collections:
            if not client.collection_exists(collection_name=col):
                client.create_collection(
                    collection_name=col,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
    except Exception as e:
        logger.error(f"Failed to setup Qdrant client: {e}")

    _rag_service_instance = RAGService(client=client)
    return _rag_service_instance
