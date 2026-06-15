import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "project": "AI News-to-Carousel Automation Platform"
    }


def test_slide_out_includes_text_zone_and_visual_type():
    """SlideOut schema should expose text_zone and visual_type."""
    from api.approvals import SlideOut

    slide_out = SlideOut(
        id=1,
        text_content="Test",
        caption="Caption",
        emoji="🔥",
        image_url="http://example.com/img.webp",
        text_zone="center-bottom third",
        visual_type="minimalist",
    )
    assert slide_out.text_zone == "center-bottom third"
    assert slide_out.visual_type == "minimalist"


def test_project_create_has_style_preset():
    """ProjectCreate schema should accept style_preset with default value."""
    from schemas.project import ProjectCreate

    pc = ProjectCreate(
        name="Test",
        industry="technology",
        keywords=["test"],
    )
    # style_preset should default to "general_soft"
    assert pc.style_preset == "general_soft"
    # explicit override should work
    pc2 = ProjectCreate(
        name="Test",
        industry="technology",
        keywords=["test"],
        style_preset="tech_editorial",
    )
    assert pc2.style_preset == "tech_editorial"


def test_project_response_has_style_preset_field():
    """ProjectResponse schema should include style_preset field."""
    from schemas.project import ProjectResponse

    # Just check the field exists in the schema
    assert "style_preset" in ProjectResponse.model_fields


def test_pending_approval_includes_new_slide_fields():
    """The /pending endpoint response should include text_zone and visual_type in slides."""
    # This is a schema-level test since we can't easily hit the endpoint
    from api.approvals import SlideOut
    from typing import get_type_hints

    hints = get_type_hints(SlideOut)
    assert "text_zone" in hints, f"SlideOut missing text_zone, has {list(hints)}"
    assert "visual_type" in hints, f"SlideOut missing visual_type, has {list(hints)}"
