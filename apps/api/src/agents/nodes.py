import json
from src.agents.state import GraphState, ArticleData, SlideData
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import get_settings

from src.services.search.tavily import TavilySearchService

settings = get_settings()

def get_llm():
    return ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)

# We initialize the service here for simplicity, but it could be injected via config or LangGraph state
search_service = TavilySearchService(api_key=settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None

def research_agent(state: GraphState) -> GraphState:
    """Discovers trending and relevant news articles."""
    queries = state.get("search_queries", [])
    if not queries:
        queries = state["keywords"]
    
    articles = []
    
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
            results = search_service.search(query=query, max_results=3)
            articles.extend(results)
            
    return {**state, "current_articles": articles}

def verification_agent(state: GraphState) -> GraphState:
    """Evaluates article quality and relevance."""
    articles = state.get("current_articles", [])
    approved = []
    
    # Mocking Verification logic > 7.0 score
    for idx, article in enumerate(articles):
        # We approve the first one or if we have less than 3
        if idx < 2:
            approved.append(article)
            
    return {**state, "approved_articles": approved}

def query_refinement_agent(state: GraphState) -> GraphState:
    """Improves search quality after verification failures."""
    retries = state.get("retries", 0) + 1
    new_queries = [f"{kw} latest news" for kw in state["keywords"]]
    return {**state, "retries": retries, "search_queries": new_queries}

def content_generation_agent(state: GraphState) -> GraphState:
    """Converts approved articles into carousel content."""
    approved_articles = state.get("approved_articles", [])
    generated = {}
    
    for article in approved_articles:
        # Mocking generation
        generated[article["url"]] = [
            {"text_content": f"Slide 1: {article['title']}", "image_prompt": "Futuristic abstract background"},
            {"text_content": f"Slide 2: {article['summary']}", "image_prompt": "Tech illustration"},
        ]
        
    return {**state, "generated_slides": generated}

def slide_verification_agent(state: GraphState) -> GraphState:
    """Validates generated content before rendering."""
    generated = state.get("generated_slides", {})
    approved = {}
    
    for url, slides in generated.items():
        # Checking character limit (mock check)
        valid_slides = []
        for slide in slides:
            if len(slide["text_content"]) < 200:
                valid_slides.append(slide)
        approved[url] = valid_slides
        
    return {**state, "approved_slides": approved}

def publishing_agent(state: GraphState) -> GraphState:
    """Publishes approved content."""
    # This is a stub for the publishing API
    return {**state, "publish_status": "Success"}
