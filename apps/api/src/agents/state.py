from typing import List, Dict, Any, Literal, Optional, TypedDict
import operator

class ArticleData(TypedDict):
    title: str
    url: str
    source: str
    published_date: str
    summary: str

TextZone = Literal[
    "center-bottom third",
    "full center",
    "lower-left aligned",
    "right half clear",
]

VisualType = Literal["minimalist", "thematic", "generative"]

class SlideData(TypedDict):
    hook_type: str       # "question" | "statistic" | "bold_claim" | "story" | "cta"
    text_content: str    # Main copy (up to 280 chars)
    caption: str         # Supporting context or subtitle
    image_prompt: str    # Detailed, style-specific image generation prompt
    emoji: str           # Contextual emoji for visual punch
    text_zone: TextZone  # Where the overlay text will land
    visual_type: VisualType  # Per-slide cost tier

class GraphState(TypedDict):
    project_id: int
    keywords: List[str]
    industry: str
    
    # Research state
    search_queries: List[str]
    current_articles: List[ArticleData]
    retries: int
    
    # Verification state
    approved_articles: List[ArticleData]
    
    # Generation state
    generated_slides: Dict[str, List[SlideData]] # url -> slides
    
    # Slide verification state
    approved_slides: Dict[str, List[SlideData]]
    
    # Publishing State
    publish_status: str
