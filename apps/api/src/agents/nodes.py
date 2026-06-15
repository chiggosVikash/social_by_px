import json
import logging
from typing import Any
from .state import GraphState, ArticleData, SlideData
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.config import get_settings

# ── Import all prompts from the prompt system ──
from .prompts import (
    build_generation_system_prompt,
    build_generation_user_prompt,
    build_refinement_system_prompt,
    build_verification_prompt,
    build_article_verification_prompt,
    build_query_refinement_prompt,
)

logger = logging.getLogger(__name__)

class ChatGeminiResponse:
    def __init__(self, content: str):
        self.content = content

class ChatGeminiGemma:
    """
    Custom client to interact with Google Gemini/Gemma API using httpx,
    mimicking the LangChain ChatOpenAI invoke interface.
    """
    def __init__(self, model: str, api_key: str, temperature: float = 0.7):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature

    def invoke(self, messages) -> ChatGeminiResponse:
        import httpx
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        system_instruction = None
        contents = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_instruction = {
                    "parts": [{"text": msg.content}]
                }
            elif isinstance(msg, HumanMessage):
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
            elif isinstance(msg, AIMessage):
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })
            else:
                role = getattr(msg, "type", "user")
                if role == "system":
                    system_instruction = {
                        "parts": [{"text": getattr(msg, "content", str(msg))}]
                    }
                else:
                    role_name = "user" if role == "human" else "model"
                    contents.append({
                        "role": role_name,
                        "parts": [{"text": getattr(msg, "content", str(msg))}]
                    })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        try:
            logger.info(f"Calling Gemini API with model: {self.model}")
            resp = httpx.post(url, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            resp_data = resp.json()
            
            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"Gemini API returned no candidates. Response: {resp_data}")
                
            candidate = candidates[0]
            content_obj = candidate.get("content", {})
            parts = content_obj.get("parts", [])
            if not parts:
                raise RuntimeError(f"Gemini API candidate content has no parts. Response: {resp_data}")
                
            text = parts[0].get("text", "")
            return ChatGeminiResponse(content=text)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise RuntimeError(f"Gemini API call failed: {e}")

# [PATTERN: Strategy] — Chooses LLM provider based on configured API keys
def get_llm(temperature: float = 0.7):
    settings = get_settings()
    
    # 1. OpenRouter (highest priority if configured)
    if getattr(settings, 'OPENROUTER_API_KEY', None):
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            model=getattr(settings, 'OPENROUTER_MODEL', "meta-llama/llama-3-70b-instruct"),
            temperature=temperature
        )

    # 2. Gemini API Key
    api_key = settings.GEMINI_API_KEY
    if api_key:
        model = settings.GEMINI_MODEL or "gemma-4-31b-it"
        return ChatGeminiGemma(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
        
    # 3. Fallback to OpenAI
    return ChatOpenAI(
        model="gpt-4o", 
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature
    )

def get_search_service():
    settings = get_settings()
    if settings.TAVILY_API_KEY:
        from services.search.tavily import TavilySearchService
        return TavilySearchService(api_key=settings.TAVILY_API_KEY)
    return None

TRUSTED_DOMAINS_BY_INDUSTRY = {
    "technology": ["techcrunch.com", "wired.com", "theverge.com", "arstechnica.com", "venturebeat.com"],
    "startup":    ["techcrunch.com", "forbes.com", "inc.com", "entrepreneur.com", "ycombinator.com"],
    "finance":    ["bloomberg.com", "reuters.com", "ft.com", "wsj.com", "economictimes.indiatimes.com"],
    "health":     ["who.int", "healthline.com", "medscape.com", "nih.gov", "webmd.com"],
    "marketing":  ["marketingweek.com", "adage.com", "hubspot.com", "searchengineland.com"],
    "education":  ["edtech.com", "edsurge.com", "chronicle.com", "timeshighereducation.com"],
}

BLOCKED_DOMAINS = [
    "imdb.com", "wikipedia.org", "quora.com", "reddit.com",
    "youtube.com", "pinterest.com", "instagram.com", "twitter.com",
    "amazon.com", "ebay.com", "craigslist.com",
]

def research_agent(state: GraphState) -> GraphState:
    """Discovers trending and relevant news articles."""
    queries = state.get("search_queries", [])
    if not queries:
        queries = state["keywords"]
    
    industry = state.get("industry", "general")
    trusted_domains = TRUSTED_DOMAINS_BY_INDUSTRY.get(industry.lower(), [])
    
    articles = []
    
    search_service = get_search_service()
    if not search_service:
        # Mock articles if no service is configured
        articles.append({
            "title": "AI is taking over the world",
            "url": "https://example.com/ai-news",
            "source": "TechCrunch",
            "published_date": "2026-06-11",
            "summary": "AI is advancing rapidly."
        })
    else:
        for query in queries:
            results = search_service.search(
                query=query, 
                max_results=3,
                topic="news",
                days=7,
                include_domains=trusted_domains if trusted_domains else None,
                exclude_domains=BLOCKED_DOMAINS
            )
            articles.extend(results)
            
    return {**state, "current_articles": articles}

def verification_agent(state: GraphState) -> GraphState:
    """Evaluates article quality and relevance."""
    articles = state.get("current_articles", [])
    keywords = state.get("keywords", [])
    industry = state.get("industry", "general")
    platform = state.get("platform", "instagram")
    approved = []
    rejection_reasons = []
    
    llm = get_llm(temperature=0.1)
    
    for article in articles:
        try:
            prompt = build_article_verification_prompt(
                article=article,
                keywords=keywords,
                industry=industry,
                platform=platform
            )
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            result = _parse_llm_json(response.content)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if isinstance(result, dict) and result.get("approve"):
                approved.append(article)
            elif isinstance(result, dict) and result.get("reject_reason"):
                rejection_reasons.append(f"{article['url']}: {result.get('reject_reason')}")
            else:
                rejection_reasons.append(f"{article['url']}: Failed to parse LLM response")
        except Exception as e:
            logger.error(f"Verification failed for {article['url']}: {e}")
            rejection_reasons.append(f"{article['url']}: Error {str(e)}")
            
    return {**state, "approved_articles": approved, "rejection_reasons": rejection_reasons}

def rag_retrieval_agent(state: GraphState) -> GraphState:
    """Retrieves domain and creator style context from Qdrant."""
    creator_id = state.get("creator_id")
    keywords = state.get("keywords", [])
    industry = state.get("industry", "")
    
    if creator_id:
        from services.rag import get_rag_service
        rag_service = get_rag_service()
        context = rag_service.retrieve_context(creator_id, keywords, industry)
        if context:
            return {**state, "rag_context": context}
    return {**state, "rag_context": ""}

def query_refinement_agent(state: GraphState) -> GraphState:
    """Generates better search queries after verification failures."""
    retries = state.get("retries", 0) + 1

    llm = get_llm(temperature=0.4)
    prompt = build_query_refinement_prompt(
        topic=", ".join(state.get("keywords", [])),
        keywords=state.get("keywords", []),
        industry=state.get("industry", "general"),
        content_angle=state.get("content_angle", "Latest News & Updates"),
        audience=state.get("audience", "general"),
        failed_queries=state.get("search_queries", state.get("keywords", [])),
        rejection_reasons=state.get("rejection_reasons", [])
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = _parse_llm_json(response.content)
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
            
        new_queries = result.get("queries", [])
        if not new_queries:
            raise ValueError("No queries returned")
    except Exception as e:
        logger.error(f"Query refinement failed: {e}")
        new_queries = [f"{kw} latest news" for kw in state.get("keywords", [])]

    return {**state, "retries": retries, "search_queries": new_queries}

# [DRY] — extracted JSON parsing; reused in both generation passes
def _parse_llm_json(raw_content) -> Any:
    """Parse JSON from LLM response, handling markdown code fences and conversational text."""
    import re
    if not isinstance(raw_content, str):
        raw_content = raw_content[0].get("text", "") if isinstance(raw_content, list) and isinstance(raw_content[0], dict) else str(raw_content)
    content = raw_content.strip()
    
    # Try to find a JSON block (array or object)
    match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
    if match:
        content = match.group(0)
    else:
        # Fallback to standard stripping
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
    return json.loads(content.strip())


def content_generation_agent(state: GraphState) -> GraphState:
    """Converts approved articles into premium carousel content using two-pass generation."""
    approved_articles = state.get("approved_articles", [])
    industry = state.get("industry", "general")
    audience = state.get("audience", "general")
    tone = state.get("tone", "")
    content_angle = state.get("content_angle", "Latest News & Updates")
    platform = state.get("platform", "instagram")
    language = state.get("language", "english")
    rag_context = state.get("rag_context", "")
    slide_count = state.get("slide_count", 5)
    generated = state.get("generated_slides", {})
    approved_slides = state.get("approved_slides", {})

    for article in approved_articles:
        url = article["url"]
        if url in approved_slides:
            # Already generated and verified, skip
            continue
            
        llm = get_llm(temperature=0.7)

        # --- Pass 1: Draft generation ---
        sys_prompt_1 = build_generation_system_prompt(
            industry=industry,
            audience=audience,
            tone=tone,
            content_angle=content_angle,
            platform=platform,
            language=language,
            slide_count=slide_count,
            creator_style=rag_context,
        )
        usr_prompt_1 = build_generation_user_prompt(
            article=article,
            slide_count=slide_count,
            audience=audience,
            tone=tone,
            language=language,
            industry=industry,
        )
        
        draft_messages = [
            SystemMessage(content=sys_prompt_1),
            HumanMessage(content=usr_prompt_1)
        ]

        draft_response = llm.invoke(draft_messages)
        draft_slides = _parse_llm_json(draft_response.content)

        # --- Pass 2: Refinement ---
        sys_prompt_2 = build_refinement_system_prompt(
            industry=industry,
            audience=audience,
            tone=tone,
            content_angle=content_angle,
            platform=platform,
            language=language,
            article=article
        )
        refine_messages = [
            SystemMessage(content=sys_prompt_2),
            HumanMessage(content=json.dumps(draft_slides, indent=2))
        ]

        refined_response = llm.invoke(refine_messages)
        refined_slides = _parse_llm_json(refined_response.content)
        generated[article["url"]] = refined_slides

    return {**state, "generated_slides": generated}


def slide_verification_agent(state: GraphState) -> GraphState:
    """Validates generated content quality before publishing."""
    generated = state.get("generated_slides", {})
    industry = state.get("industry", "general")
    audience = state.get("audience", "general")
    tone = state.get("tone", "")
    content_angle = state.get("content_angle", "Latest News & Updates")
    platform = state.get("platform", "instagram")
    language = state.get("language", "english")
    slide_count = state.get("slide_count", 5)
    
    approved = {}
    
    # Need article lookup by URL to get title and summary
    articles_by_url = {a["url"]: a for a in state.get("approved_articles", [])}

    llm = get_llm(temperature=0.1)

    for url, slides in generated.items():
        article = articles_by_url.get(url, {})
        
        prompt = build_verification_prompt(
            slides=slides,
            article=article,
            industry=industry,
            audience=audience,
            tone=tone,
            content_angle=content_angle,
            platform=platform,
            language=language,
            slide_count=slide_count
        )
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            result = _parse_llm_json(response.content)
            
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
                
            if isinstance(result, dict) and result.get("passed"):
                approved[url] = slides
            else:
                logger.warning(f"Slide verification failed for {url}: {result.get('failed_checks', [])}")
        except Exception as e:
            logger.error(f"Slide verification failed to parse LLM response for {url}: {e}")
            
    if not approved or len(approved) < len(articles_by_url):
        current_retries = state.get("slide_retries", 0)
        return {**state, "approved_slides": approved, "slide_retries": current_retries + 1}
            
    return {**state, "approved_slides": approved}


def publishing_agent(state: GraphState) -> GraphState:
    """Publishes approved content."""
    # This is a stub for the publishing API
    return {**state, "publish_status": "Success"}

