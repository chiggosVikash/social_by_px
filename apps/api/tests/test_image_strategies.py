import base64
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from services.image import (
    SlideImageStrategyFactory,
    DalleSlideImageStrategy,
    TemplateCompositingSlideImageStrategy,
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
        emoji="✨"
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


def test_strategy_factory(mock_project_dalle, mock_project_template):
    # Test factory returns Dalle strategy
    strategy = SlideImageStrategyFactory.get_strategy(mock_project_dalle)
    assert isinstance(strategy, DalleSlideImageStrategy)

    # Test factory returns Template strategy
    strategy = SlideImageStrategyFactory.get_strategy(mock_project_template)
    assert isinstance(strategy, TemplateCompositingSlideImageStrategy)


@pytest.mark.asyncio
@patch("services.image.get_image_generation_service")
@patch("services.storage.upload_file", new_callable=AsyncMock)
async def test_dalle_slide_image_strategy(mock_upload_file, mock_get_image_service, mock_db, mock_slide, mock_article, mock_project_dalle):
    # Setup mocks
    mock_service = AsyncMock()
    mock_service.generate.return_value = b"raw_dalle_bytes"
    mock_get_image_service.return_value = mock_service
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
        mock_service.generate.assert_called_once()
        mock_optimize.assert_called_once_with(b"raw_dalle_bytes", quality=80)
        mock_upload_file.assert_called_once()


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


from services.image import (
    GptImage1MiniStrategy,
    get_image_generation_service,
)


@pytest.fixture
def mock_gpt_image_response():
    """Build a mock response that mimics openai.types.images_response.ImageResponse."""
    mock_data_item = MagicMock()
    mock_data_item.b64_json = base64.b64encode(b"fake_png_bytes").decode()

    mock_response = MagicMock()
    mock_response.data = [mock_data_item]
    return mock_response


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_happy_path(mock_openai_cls, mock_gpt_image_response):
    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_gpt_image_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("a blue gradient background")

    assert result == b"fake_png_bytes"
    mock_client.images.generate.assert_called_once_with(
        model="gpt-image-1-mini",
        prompt="a blue gradient background",
        size="1024x1024",
        quality="medium",
        n=1,
        response_format="b64_json",
    )


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_api_error(mock_openai_cls):
    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(side_effect=RuntimeError("API down"))
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_empty_data(mock_openai_cls):
    mock_response = MagicMock()
    mock_response.data = []

    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_missing_b64_json(mock_openai_cls):
    mock_data_item = MagicMock()
    mock_data_item.b64_json = None

    mock_response = MagicMock()
    mock_response.data = [mock_data_item]

    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


def test_factory_returns_gpt_image_1_mini_strategy():
    service = get_image_generation_service()
    assert type(service._strategy).__name__ == "GptImage1MiniStrategy"


@pytest.mark.asyncio
async def test_gpt_image_1_mini_full_path_live():
    """Optional: live API test. Only runs when OPENAI_API_KEY is set and LIVE_API_TESTS=1."""
    import os
    if not os.environ.get("OPENAI_API_KEY") or os.environ.get("LIVE_API_TESTS") != "1":
        pytest.skip("Live API test skipped — set OPENAI_API_KEY and LIVE_API_TESTS=1 to run")

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image(
        "Soft, even lighting. No text, no people, no objects. "
        "Clean gradient or abstract pattern. Suitable for white text overlay. "
        "Modern editorial style. Theme: artificial intelligence"
    )
    assert result is not None
    assert len(result) > 1000  # should be a real image
