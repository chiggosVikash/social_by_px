import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from services.renderer import composite_text_on_background

@pytest.mark.asyncio
async def test_composite_text_on_background():
    # 1. Create a dummy background image bytes
    bg_img = Image.new("RGB", (500, 800), color="blue")
    bg_bytes = io.BytesIO()
    bg_img.save(bg_bytes, format="JPEG")
    bg_bytes = bg_bytes.getvalue()
    
    # 2. Mock httpx.get to return our dummy background image
    with patch("services.renderer.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = bg_bytes
        mock_get.return_value = mock_response
        
        # 3. Call the composite function
        rendered_bytes = await composite_text_on_background(
            text_content="Hello world this is a test slide content",
            emoji="🚀",
            caption="Supporting context subtitle",
            background_url="http://example.com/test-bg.jpg",
            slide_index=0,
            total_slides=5
        )
        
        # 4. Assertions
        assert isinstance(rendered_bytes, bytes)
        assert len(rendered_bytes) > 0
        
        # Verify it is a valid WebP image of exactly 1080x1080
        out_img = Image.open(io.BytesIO(rendered_bytes))
        assert out_img.format == "WEBP"
        assert out_img.size == (1080, 1080)


@pytest.mark.asyncio
async def test_composite_text_on_background_r2_direct():
    # 1. Create a dummy background image bytes
    bg_img = Image.new("RGB", (500, 800), color="red")
    bg_bytes = io.BytesIO()
    bg_img.save(bg_bytes, format="JPEG")
    bg_bytes = bg_bytes.getvalue()

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.CLOUDFLARE_R2_ACCESS_KEY_ID = "test-key"
    mock_settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY = "test-secret"
    mock_settings.CLOUDFLARE_R2_ENDPOINT_URL = "https://mock-endpoint.r2.cloudflarestorage.com"
    mock_settings.CLOUDFLARE_R2_BUCKET_NAME = "mock-bucket"

    # Mock S3 Client
    mock_s3_client = MagicMock()
    mock_response = {
        'Body': MagicMock(read=lambda: bg_bytes)
    }
    mock_s3_client.get_object.return_value = mock_response

    with patch("core.config.get_settings", return_value=mock_settings), \
         patch("services.storage.get_s3_client", return_value=mock_s3_client) as mock_get_s3, \
         patch("services.renderer.httpx.get") as mock_httpx_get:

        # 3. Call the composite function with a URL starting with mock-endpoint
        rendered_bytes = await composite_text_on_background(
            text_content="Slide content with R2 download",
            emoji="🍕",
            caption="Direct download test",
            background_url="https://mock-endpoint.r2.cloudflarestorage.com/mock-bucket/projects/project_11_background_921b53ad.jpg",
            slide_index=0,
            total_slides=5
        )

        # Verify S3 client was used and httpx was NOT used
        mock_get_s3.assert_called_once()
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="mock-bucket",
            Key="projects/project_11_background_921b53ad.jpg"
        )
        mock_httpx_get.assert_not_called()

        # Verify output is a valid WebP image of exactly 1080x1080
        out_img = Image.open(io.BytesIO(rendered_bytes))
        assert out_img.format == "WEBP"
        assert out_img.size == (1080, 1080)


@pytest.mark.asyncio
async def test_composite_text_on_background_r2_public_direct():
    # 1. Create a dummy background image bytes
    bg_img = Image.new("RGB", (500, 800), color="green")
    bg_bytes = io.BytesIO()
    bg_img.save(bg_bytes, format="JPEG")
    bg_bytes = bg_bytes.getvalue()

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.CLOUDFLARE_R2_ACCESS_KEY_ID = "test-key"
    mock_settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY = "test-secret"
    mock_settings.CLOUDFLARE_R2_ENDPOINT_URL = "https://mock-endpoint.r2.cloudflarestorage.com"
    mock_settings.CLOUDFLARE_R2_BUCKET_NAME = "mock-bucket"
    mock_settings.CLOUDFLARE_R2_PUBLIC_URL = "https://pub-mock.r2.dev"

    # Mock S3 Client
    mock_s3_client = MagicMock()
    mock_response = {
        'Body': MagicMock(read=lambda: bg_bytes)
    }
    mock_s3_client.get_object.return_value = mock_response

    with patch("core.config.get_settings", return_value=mock_settings), \
         patch("services.storage.get_s3_client", return_value=mock_s3_client) as mock_get_s3, \
         patch("services.renderer.httpx.get") as mock_httpx_get:

        # 3. Call the composite function with a public dev URL
        rendered_bytes = await composite_text_on_background(
            text_content="Slide content with R2 public download",
            emoji="🍣",
            caption="Public direct download test",
            background_url="https://pub-mock.r2.dev/projects/project_11_background_921b53ad.jpg",
            slide_index=0,
            total_slides=5
        )

        # Verify S3 client was used and httpx was NOT used
        mock_get_s3.assert_called_once()
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="mock-bucket",
            Key="projects/project_11_background_921b53ad.jpg"
        )
        mock_httpx_get.assert_not_called()

        # Verify output is a valid WebP image of exactly 1080x1080
        out_img = Image.open(io.BytesIO(rendered_bytes))
        assert out_img.format == "WEBP"
        assert out_img.size == (1080, 1080)


@pytest.mark.asyncio
async def test_composite_text_on_background_accepts_bytes():
    """Renderer should accept background_bytes directly."""
    from services.renderer import composite_text_on_background

    # Make a 1080x1080 cream image
    img = Image.new("RGB", (1080, 1080), color=(245, 241, 232))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    bg_bytes = buf.getvalue()

    result = await composite_text_on_background(
        text_content="Hello",
        emoji="🔥",
        caption="Subtitle",
        background_url=None,
        background_bytes=bg_bytes,
        text_zone="center-bottom third",
        slide_index=0,
        total_slides=1,
    )
    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_composite_text_on_background_raises_when_no_background():
    """Renderer should raise ValueError when neither url nor bytes provided."""
    from services.renderer import composite_text_on_background

    with pytest.raises(ValueError, match="background"):
        await composite_text_on_background(
            text_content="Hello",
            emoji=None,
            caption=None,
            background_url=None,
            background_bytes=None,
            text_zone="center-bottom third",
        )


@pytest.mark.asyncio
async def test_composite_text_on_background_supports_all_zones():
    """Renderer should accept all 4 valid text zones."""
    from services.renderer import composite_text_on_background

    img = Image.new("RGB", (1080, 1080), color=(245, 241, 232))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    bg_bytes = buf.getvalue()

    for zone in ["center-bottom third", "full center", "lower-left aligned", "right half clear"]:
        result = await composite_text_on_background(
            text_content="Test",
            emoji=None,
            caption=None,
            background_url=None,
            background_bytes=bg_bytes,
            text_zone=zone,
            slide_index=0,
            total_slides=1,
        )
        assert isinstance(result, bytes)


