import pytest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from services.image import (
    SlideImageStrategyFactory,
    DalleSlideImageStrategy,
    TemplateCompositingSlideImageStrategy,
    ProgrammaticPILStrategy,
    ImageOptimizationService
)

class DummyModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_slide():
    return DummyModel(
        id=123,
        text_content="Slide Main Text Content",
        caption="Slide Supporting Caption",
        emoji="✨",
        text_zone="center",
        image_prompt="Abstract blue and white background for a social media slide",
    )

@pytest.fixture
def mock_article():
    return DummyModel(
        id=456,
        title="Test Article Title"
    )

@pytest.fixture
def mock_project_dalle():
    return DummyModel(
        id=789,
        avoid_image_generation=False,
        background_image_url=None
    )

@pytest.fixture
def mock_project_template():
    return DummyModel(
        id=789,
        avoid_image_generation=True,
        background_image_url="http://localhost:8000/static/bg.jpg"
    )


def test_strategy_factory_dispatches_on_visual_type():
    """Factory dispatches on visual_type string and returns the correct strategy class."""
    # minimalist -> ProgrammaticPILStrategy
    strategy = SlideImageStrategyFactory.get_strategy("minimalist")
    assert isinstance(strategy, ProgrammaticPILStrategy)

    # thematic -> TemplateCompositingSlideImageStrategy
    strategy = SlideImageStrategyFactory.get_strategy("thematic")
    assert isinstance(strategy, TemplateCompositingSlideImageStrategy)

    # generative -> DalleSlideImageStrategy
    strategy = SlideImageStrategyFactory.get_strategy("generative")
    assert isinstance(strategy, DalleSlideImageStrategy)


def test_factory_raises_on_unknown_visual_type():
    """Factory raises ValueError for unknown visual_type strings."""
    with pytest.raises(ValueError, match="Unknown visual_type"):
        SlideImageStrategyFactory.get_strategy("unknown_type")


def test_factory_raises_on_none_visual_type():
    """Factory raises ValueError when visual_type is None or missing."""
    with pytest.raises(ValueError, match="Unknown visual_type"):
        SlideImageStrategyFactory.get_strategy(None)

    with pytest.raises(ValueError, match="Unknown visual_type"):
        SlideImageStrategyFactory.get_strategy("")


@pytest.mark.asyncio
@patch("services.image.get_image_generation_service")
@patch("services.renderer.composite_text_on_background", new_callable=AsyncMock)
@patch("services.storage.upload_file", new_callable=AsyncMock)
async def test_dalle_slide_image_strategy(mock_upload_file, mock_composite, mock_get_image_service, mock_db, mock_slide, mock_article, mock_project_dalle):
    # Setup mocks
    mock_service = AsyncMock()
    mock_service.generate.return_value = b"raw_dalle_bytes"
    mock_get_image_service.return_value = mock_service
    mock_composite.return_value = b"rendered_composite_bytes"
    mock_upload_file.return_value = "https://r2.storage/slides/123.webp"

    strategy = DalleSlideImageStrategy()

    # Mock ImageOptimizationService.optimize_for_web to return whatever was input
    with patch.object(ImageOptimizationService, "optimize_for_web", return_value=b"optimized_webp_bytes") as mock_optimize:
        url = await strategy.generate_and_save(
            db=mock_db,
            slide=mock_slide,
            article=mock_article,
            project=mock_project_dalle,
            idx=0,
            total=5
        )

        assert url == "https://r2.storage/slides/123.webp"
        # Verify the prompt passed to the image service includes the text_zone constraint
        call_args = mock_service.generate.call_args
        prompt = call_args[0][0]
        assert "CENTER" in prompt.upper(), f"Prompt should contain text_zone constraint, got: {prompt}"
        assert "DO NOT include any text" in prompt
        assert "STYLE LOCK" in prompt
        mock_optimize.assert_called_once()
        mock_composite.assert_called_once()
        mock_upload_file.assert_called_once()


@pytest.mark.asyncio
@patch("services.image.get_image_generation_service")
async def test_dalle_prompt_includes_text_zone_constraint(mock_get_image_service, mock_slide, mock_article, mock_project_dalle):
    """The composed prompt must include the slide's text_zone constraint."""
    mock_service = AsyncMock()
    mock_service.generate.return_value = b"raw_dalle_bytes"
    mock_get_image_service.return_value = mock_service

    strategy = DalleSlideImageStrategy()
    with patch.object(ImageOptimizationService, "optimize_for_web", return_value=b"x"), \
         patch("services.renderer.composite_text_on_background", new_callable=AsyncMock, return_value=b"x"), \
         patch("services.storage.upload_file", new_callable=AsyncMock, return_value="https://r2/test.webp"):
        await strategy.generate_and_save(
            db=MagicMock(),
            slide=mock_slide,
            article=mock_article,
            project=mock_project_dalle,
            idx=0,
            total=1,
        )

        prompt_arg = mock_service.generate.call_args[0][0]
        assert "CENTER" in prompt_arg.upper()


@pytest.mark.asyncio
@patch("services.renderer.composite_text_on_background", new_callable=AsyncMock)
@patch("services.storage.upload_file", new_callable=AsyncMock)
async def test_template_compositing_slide_image_strategy(mock_upload_file, mock_composite, mock_db, mock_slide, mock_article, mock_project_template):
    # Setup mocks
    mock_composite.return_value = b"rendered_composite_bytes"
    mock_upload_file.return_value = "https://r2.storage/slides/123_composite.webp"

    strategy = TemplateCompositingSlideImageStrategy()
    
    url = await strategy.generate_and_save(
        db=mock_db,
        slide=mock_slide,
        article=mock_article,
        project=mock_project_template,
        idx=2,
        total=5
    )
    
    assert url == "https://r2.storage/slides/123_composite.webp"
    mock_composite.assert_called_once_with(
        text_content=mock_slide.text_content,
        emoji=mock_slide.emoji,
        caption=mock_slide.caption,
        background_url=mock_project_template.background_image_url,
        slide_index=2,
        total_slides=5
    )
    mock_upload_file.assert_called_once_with(b"rendered_composite_bytes", ANY, content_type="image/webp")


@pytest.mark.asyncio
async def test_template_compositing_missing_background_error(mock_db, mock_slide, mock_article):
    # Setup project with avoid_image_generation but NO background image url
    invalid_project = DummyModel(
        id=789,
        avoid_image_generation=True,
        background_image_url=None
    )
    
    strategy = TemplateCompositingSlideImageStrategy()
    with pytest.raises(ValueError, match="No background image template uploaded for project"):
        await strategy.generate_and_save(
            db=mock_db,
            slide=mock_slide,
            article=mock_article,
            project=invalid_project,
            idx=0,
            total=5
        )
