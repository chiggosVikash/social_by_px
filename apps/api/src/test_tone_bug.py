import asyncio
import sys
import json
from agents.nodes import content_generation_agent, slide_verification_agent
from agents.state import GraphState

def test_full_pipeline():
    state: GraphState = {
        "project_id": 1,
        "creator_id": 1,
        "keywords": ["AI", "Startups"],
        "industry": "technology",
        "audience": "founders",
        "tone": "",
        "content_angle": "Latest News & Updates",
        "platform": "instagram",
        "language": "english",
        "slide_count": 5,
        "rag_context": "",
        "search_queries": [],
        "current_articles": [],
        "retries": 0,
        "approved_articles": [{
            "title": "AI is redefining how startups scale",
            "url": "https://www.commonfund.org/cf-private-equity/ai-is-redefining-how-startups-scale",
            "summary": "AI is helping startups scale faster by automating key tasks. Startups leveraging AI see a 40% reduction in operational costs. This shift is changing the landscape of early-stage investing.",
            "source": "Commonfund",
            "published_date": "2024-01-01"
        }],
        "rejection_reasons": [],
        "generated_slides": {},
        "approved_slides": {},
        "publish_status": ""
    }
    
    print("Running generation agent...")
    state = content_generation_agent(state)
    print("\nGenerated slides:")
    print(json.dumps(state.get("generated_slides"), indent=2))
    
    print("\nRunning verification agent...")
    new_state = slide_verification_agent(state)
    print("\nVerification result (approved_slides):")
    print(json.dumps(new_state.get("approved_slides"), indent=2))

if __name__ == "__main__":
    test_full_pipeline()
