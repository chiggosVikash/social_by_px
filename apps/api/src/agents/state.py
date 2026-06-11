from typing import List, Dict, Any, Optional, TypedDict
import operator

class ArticleData(TypedDict):
    title: str
    url: str
    source: str
    published_date: str
    summary: str

class SlideData(TypedDict):
    text_content: str
    image_prompt: str

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
