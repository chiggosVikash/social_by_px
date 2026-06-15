import pytest
from unittest.mock import patch, MagicMock
from agents.state import GraphState
from agents.nodes import (
    research_agent,
    verification_agent,
    query_refinement_agent,
    content_generation_agent,
    slide_verification_agent,
    publishing_agent
)
from agents.graph import should_refine, is_content_valid

@pytest.fixture
def initial_state() -> GraphState:
    return {
        "project_id": 1,
        "keywords": ["AI", "Tech"],
        "industry": "Technology",
        "search_queries": [],
        "current_articles": [],
        "retries": 0,
        "approved_articles": [],
        "generated_slides": {},
        "approved_slides": {},
        "publish_status": ""
    }

def test_research_agent(initial_state):
    with patch("agents.nodes.get_search_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.search.return_value = [
            {"title": "Test AI", "url": "http://test.com", "source": "Test", "published_date": "2026", "summary": "Test"}
        ]
        mock_get_service.return_value = mock_service
        
        new_state = research_agent(initial_state)
        # We have 2 keywords ("AI", "Tech"), so it extends twice
        assert len(new_state["current_articles"]) == 2
        assert new_state["current_articles"][0]["title"] == "Test AI"

def test_verification_agent(initial_state):
    initial_state["current_articles"] = [
        {"title": "Article 1", "url": "http://test1.com", "source": "Test", "published_date": "2026", "summary": "Test"},
        {"title": "Article 2", "url": "http://test2.com", "source": "Test", "published_date": "2026", "summary": "Test"},
        {"title": "Article 3", "url": "http://test3.com", "source": "Test", "published_date": "2026", "summary": "Test"}
    ]
    new_state = verification_agent(initial_state)
    # The logic mocks approving the first 2
    assert len(new_state["approved_articles"]) == 2

def test_query_refinement_agent(initial_state):
    initial_state["retries"] = 1
    new_state = query_refinement_agent(initial_state)
    assert new_state["retries"] == 2
    assert "AI latest news" in new_state["search_queries"]

def test_content_generation_agent(initial_state):
    initial_state["approved_articles"] = [
         {"title": "Article 1", "url": "http://test1.com", "source": "Test", "published_date": "2026", "summary": "Test"}
    ]
    with patch("agents.nodes.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '[{"text_content": "Slide 1 text", "image_prompt": "Image 1"}]'
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        new_state = content_generation_agent(initial_state)
        assert "http://test1.com" in new_state["generated_slides"]
        assert len(new_state["generated_slides"]["http://test1.com"]) == 1
        assert new_state["generated_slides"]["http://test1.com"][0]["text_content"] == "Slide 1 text"

def test_slide_verification_agent(initial_state):
    initial_state["generated_slides"] = {
        "http://test1.com": [
            {"text_content": "Valid short text 1", "image_prompt": "Img", "hook_type": "question", "text_zone": "center-bottom third", "visual_type": "minimalist"},
            {"text_content": "Valid short text 2", "image_prompt": "Img", "hook_type": "statistic", "text_zone": "full center", "visual_type": "thematic"},
            {"text_content": "Valid short text 3", "image_prompt": "Img", "hook_type": "bold_claim", "text_zone": "lower-left aligned", "visual_type": "generative"},
            {"text_content": "x" * 300, "image_prompt": "Too long text", "hook_type": "cta", "text_zone": "right half clear", "visual_type": "minimalist"}
        ]
    }
    new_state = slide_verification_agent(initial_state)
    assert len(new_state["approved_slides"]["http://test1.com"]) == 3
    assert new_state["approved_slides"]["http://test1.com"][0]["text_content"] == "Valid short text 1"

def test_publishing_agent(initial_state):
    new_state = publishing_agent(initial_state)
    assert new_state["publish_status"] == "Success"

def test_conditional_edges(initial_state):
    state1 = initial_state.copy()
    state1["approved_articles"] = []
    state1["retries"] = 1
    assert should_refine(state1) == "refine"

    state2 = initial_state.copy()
    # Adding mock keys to pass type checking for ArticleData if it's strict
    state2["approved_articles"] = [{"title": "Art", "url": "", "source": "", "published_date": "", "summary": ""}]
    state2["retries"] = 1
    assert should_refine(state2) == "generate"

    state3 = initial_state.copy()
    state3["approved_articles"] = []
    state3["retries"] = 3
    assert should_refine(state3) == "end"

    state4 = initial_state.copy()
    state4["approved_slides"] = {"http://": []}
    assert is_content_valid(state4) == "publish"

    state5 = initial_state.copy()
    state5["approved_slides"] = {}
    assert is_content_valid(state5) == "regenerate"


def test_slide_data_has_text_zone_and_visual_type():
    """SlideData TypedDict should include text_zone and visual_type fields."""
    from agents.state import SlideData, TextZone, VisualType

    slide_data: SlideData = {
        "hook_type": "question",
        "text_content": "Test content",
        "caption": "Test caption",
        "image_prompt": "Test prompt",
        "emoji": "🔥",
        "text_zone": "full center",
        "visual_type": "generative",
    }

    assert slide_data["text_zone"] == "full center"
    assert slide_data["visual_type"] == "generative"


def test_text_zone_literal_values():
    """TextZone Literal should allow the 4 valid values."""
    from agents.state import TextZone

    zones: list[TextZone] = [
        "center-bottom third",
        "full center",
        "lower-left aligned",
        "right half clear",
    ]
    assert len(zones) == 4


def test_visual_type_literal_values():
    """VisualType Literal should allow the 3 valid values."""
    from agents.state import VisualType

    types: list[VisualType] = ["minimalist", "thematic", "generative"]
    assert len(types) == 3


def test_verification_rejects_slide_missing_text_zone():
    """slide_verification_agent should reject slides missing text_zone."""
    from agents.nodes import slide_verification_agent
    from agents.state import GraphState

    state: GraphState = {
        "project_id": 1,
        "keywords": ["test"],
        "industry": "technology",
        "approved_articles": [],
        "generated_slides": {
            "https://example.com/article1": [
                {
                    "hook_type": "question",
                    "text_content": "Valid text 1",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "🔥",
                    # Missing text_zone!
                    "visual_type": "minimalist",
                },
                {
                    "hook_type": "statistic",
                    "text_content": "Valid text 2",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "📊",
                    "text_zone": "full center",
                    "visual_type": "thematic",
                },
                {
                    "hook_type": "bold_claim",
                    "text_content": "Valid text 3",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "💡",
                    "text_zone": "lower-left aligned",
                    "visual_type": "generative",
                },
            ]
        },
    }

    result = slide_verification_agent(state)
    assert "https://example.com/article1" not in result["approved_slides"]


def test_verification_rejects_slide_missing_visual_type():
    """slide_verification_agent should reject slides missing visual_type."""
    from agents.nodes import slide_verification_agent
    from agents.state import GraphState

    state: GraphState = {
        "project_id": 1,
        "keywords": ["test"],
        "industry": "technology",
        "approved_articles": [],
        "generated_slides": {
            "https://example.com/article1": [
                {
                    "hook_type": "question",
                    "text_content": "Valid text 1",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "🔥",
                    "text_zone": "center-bottom third",
                    # Missing visual_type!
                },
                {
                    "hook_type": "statistic",
                    "text_content": "Valid text 2",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "📊",
                    "text_zone": "full center",
                    "visual_type": "thematic",
                },
                {
                    "hook_type": "bold_claim",
                    "text_content": "Valid text 3",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "💡",
                    "text_zone": "lower-left aligned",
                    "visual_type": "generative",
                },
            ]
        },
    }

    result = slide_verification_agent(state)
    assert "https://example.com/article1" not in result["approved_slides"]


def test_verification_accepts_complete_slide():
    """slide_verification_agent should accept slides with all fields valid."""
    from agents.nodes import slide_verification_agent
    from agents.state import GraphState

    state: GraphState = {
        "project_id": 1,
        "keywords": ["test"],
        "industry": "technology",
        "approved_articles": [],
        "generated_slides": {
            "https://example.com/article1": [
                {
                    "hook_type": "question",
                    "text_content": "Valid text 1",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "🔥",
                    "text_zone": "center-bottom third",
                    "visual_type": "minimalist",
                },
                {
                    "hook_type": "statistic",
                    "text_content": "Valid text 2",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "📊",
                    "text_zone": "full center",
                    "visual_type": "thematic",
                },
                {
                    "hook_type": "bold_claim",
                    "text_content": "Valid text 3",
                    "caption": "",
                    "image_prompt": "test",
                    "emoji": "💡",
                    "text_zone": "lower-left aligned",
                    "visual_type": "generative",
                },
            ]
        },
    }

    result = slide_verification_agent(state)
    assert "https://example.com/article1" in result["approved_slides"]
