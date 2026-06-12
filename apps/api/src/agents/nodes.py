import json
from .state import GraphState, ArticleData, SlideData
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.config import get_settings

def get_llm():
    settings = get_settings()
    return ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)

def get_search_service():
    settings = get_settings()
    if settings.TAVILY_API_KEY:
        from services.search.tavily import TavilySearchService
        return TavilySearchService(api_key=settings.TAVILY_API_KEY)
    return None

def research_agent(state: GraphState) -> GraphState:
    """Discovers trending and relevant news articles."""
    queries = state.get("search_queries", [])
    if not queries:
        queries = state["keywords"]
    
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

# [DRY] — extracted JSON parsing; reused in both generation passes
def _parse_llm_json(raw_content) -> list:
    """Parse JSON from LLM response, handling markdown code fences."""
    if not isinstance(raw_content, str):
        raw_content = raw_content[0].get("text", "") if isinstance(raw_content, list) and isinstance(raw_content[0], dict) else str(raw_content)
    content = raw_content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return json.loads(content.strip())


# [SOLID: SRP] — industry tone mapping separated from generation logic
_INDUSTRY_TONE = {
    "technology": "authoritative and data-driven. Use precise metrics, cite breakthroughs, appeal to builders and engineers.",
    "startup": "bold and visionary. Speak founder-to-founder, emphasize disruption and opportunity.",
    "health": "empathetic and evidence-based. Lead with patient outcomes, cite research, build trust.",
    "finance": "precise and trust-building. Use concrete numbers, reference markets, project confidence.",
    "education": "inspiring and accessible. Break down complexity, celebrate learning, encourage curiosity.",
    "marketing": "punchy and conversion-focused. Lead with results, use power words, spark FOMO.",
}


def _get_tone_guidance(industry: str) -> str:
    """Return tone guidance based on industry, with a sensible default."""
    key = industry.lower().strip()
    for industry_key, tone in _INDUSTRY_TONE.items():
        if industry_key in key:
            return tone
    return "professional yet conversational. Balance insight with accessibility. Be engaging without being salesy."


_GENERATION_SYSTEM_PROMPT = """You are a world-class social media carousel content strategist. Your carousels consistently go viral because they follow a proven narrative arc.

INDUSTRY TONE: {tone}

CAROUSEL ARCHITECTURE (5 slides):
- Slide 1 (HOOK): Stop the scroll. Use a provocative question, surprising statistic, or bold claim from the article. This slide MUST make someone pause mid-scroll.
- Slide 2 (CONTEXT): Set the stage. Why does this matter RIGHT NOW? Connect to a trend, pain point, or aspiration your audience feels.
- Slide 3 (INSIGHT): Deliver the core takeaway. The one thing they'll remember and share. Make it quotable.
- Slide 4 (PROOF): Back it up. Data point, example, or real-world application that makes the insight concrete.
- Slide 5 (CTA): Drive engagement. Ask a polarizing question, invite opinions, or tease what's next. Never end with "follow for more."

RULES:
- Each slide's text_content must be 60-280 characters. Short enough to read in 3 seconds, long enough to deliver value.
- Use the article's ACTUAL data, names, and facts — do NOT make up statistics.
- Write in active voice. No passive constructions.
- Each slide must stand alone but create momentum to swipe.
- Emoji usage: 1 per slide maximum, only when it adds meaning.

RESPOND WITH ONLY a valid JSON array of 5 objects:
[
  {{
    "hook_type": "question" | "statistic" | "bold_claim" | "story" | "cta",
    "text_content": "The main copy for this slide",
    "caption": "Supporting context or subtitle (optional, keep under 100 chars)",
    "image_prompt": "A detailed prompt for generating a matching visual. Include style, mood, colors, composition.",
    "emoji": "A single emoji that fits this slide's energy"
  }}
]"""

_REFINEMENT_SYSTEM_PROMPT = """You are a senior content editor reviewing carousel slides for a {industry} brand.

Your job: sharpen every slide for MAXIMUM engagement. Apply these rules ruthlessly:

1. HOOK TEST: Would slide 1 make YOU stop scrolling? If not, rewrite it with a stronger opening.
2. CURIOSITY GAP: Does each slide make you NEED to see the next one? Add tension.
3. SPECIFICITY: Replace vague claims with concrete details from the article.
4. VOICE: Ensure the tone matches {industry} audiences — {tone}
5. CTA: The final slide should spark genuine conversation, not feel like marketing.
6. EMOJI: Verify each emoji adds meaning. Remove decorative ones.

ORIGINAL ARTICLE CONTEXT:
Title: {title}
Summary: {summary}

Review the draft slides below and return an IMPROVED version. Same JSON format, 5 slides.
Return ONLY the JSON array, no explanation."""


def content_generation_agent(state: GraphState) -> GraphState:
    """Converts approved articles into premium carousel content using two-pass generation."""
    approved_articles = state.get("approved_articles", [])
    industry = state.get("industry", "general")
    generated = {}
    tone = _get_tone_guidance(industry)

    for article in approved_articles:
        llm = get_llm()

        # --- Pass 1: Draft generation ---
        draft_messages = [
            SystemMessage(content=_GENERATION_SYSTEM_PROMPT.format(tone=tone)),
            HumanMessage(content=f"Industry: {industry}\nTitle: {article['title']}\nSource: {article.get('source', 'Unknown')}\nPublished: {article.get('published_date', 'Recent')}\nSummary: {article['summary']}")
        ]

        try:
            draft_response = llm.invoke(draft_messages)
            draft_slides = _parse_llm_json(draft_response.content)

            # --- Pass 2: Refinement ---
            refine_messages = [
                SystemMessage(content=_REFINEMENT_SYSTEM_PROMPT.format(
                    industry=industry,
                    tone=tone,
                    title=article['title'],
                    summary=article['summary']
                )),
                HumanMessage(content=json.dumps(draft_slides, indent=2))
            ]

            refined_response = llm.invoke(refine_messages)
            refined_slides = _parse_llm_json(refined_response.content)
            generated[article["url"]] = refined_slides

        except Exception as e:
            print(f"Failed to generate content for {article['url']}: {e}")
            # Structured fallback with proper slide architecture
            generated[article["url"]] = [
                {"hook_type": "bold_claim", "text_content": article['title'], "caption": f"Source: {article.get('source', 'Unknown')}", "image_prompt": f"Bold typography on dark gradient background, {industry} aesthetic, modern and clean", "emoji": "🔥"},
                {"hook_type": "story", "text_content": f"Here's why this matters for {industry} right now.", "caption": "", "image_prompt": f"Abstract visualization of {industry} trends, sleek minimal design", "emoji": "💡"},
                {"hook_type": "statistic", "text_content": article.get('summary', 'Key insight from this story.')[:280], "caption": "", "image_prompt": f"Data visualization infographic style, {industry} color palette", "emoji": "📊"},
                {"hook_type": "story", "text_content": "The implications are bigger than most people realize.", "caption": "", "image_prompt": f"Futuristic perspective shot, {industry} themed, cinematic lighting", "emoji": "🚀"},
                {"hook_type": "cta", "text_content": "What's your take? Drop your thoughts below 👇", "caption": "", "image_prompt": f"Conversation bubbles, community discussion visual, {industry} branding", "emoji": "💬"},
            ]

    return {**state, "generated_slides": generated}


def slide_verification_agent(state: GraphState) -> GraphState:
    """Validates generated content quality before publishing."""
    generated = state.get("generated_slides", {})
    approved = {}

    for url, slides in generated.items():
        valid_slides = []
        for slide in slides:
            text = slide.get("text_content", "")
            # Verify: has content, within character limit, has required fields
            if 10 < len(text) < 300 and slide.get("hook_type") and slide.get("image_prompt"):
                valid_slides.append(slide)
        # Only approve if we have at least 3 valid slides
        if len(valid_slides) >= 3:
            approved[url] = valid_slides

    return {**state, "approved_slides": approved}


def publishing_agent(state: GraphState) -> GraphState:
    """Publishes approved content."""
    # This is a stub for the publishing API
    return {**state, "publish_status": "Success"}
