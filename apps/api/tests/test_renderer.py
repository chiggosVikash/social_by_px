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
