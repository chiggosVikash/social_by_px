import base64
import io
import logging
from typing import Optional
from PIL import Image
from openai import AsyncOpenAI
from core.config import get_settings

logger = logging.getLogger(__name__)

class ImageGenerationService:
    @staticmethod
    async def generate_image(prompt: str) -> Optional[bytes]:
        """
        Generates an image using OpenAI's DALL-E model via the Responses API.
        Returns the raw image bytes if successful, None otherwise.
        """
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            logger.info("Calling OpenAI Responses API with model gpt-5.5 for image generation")
            response = await client.responses.create(
                model="gpt-5.5",
                input=prompt,
                tools=[{"type": "image_generation"}],
            )
        except Exception as api_e:
            logger.error(f"Failed to generate image with gpt-5.5: {api_e}")
            return None
            
        if not response or not response.output:
            return None

        image_data_list = [
            getattr(output, "result")
            for output in response.output
            if getattr(output, "type", "") == "image_generation_call" and hasattr(output, "result")
        ]
        
        if not image_data_list:
            logger.warning("No image generation result returned from OpenAI")
            return None
            
        image_base64 = image_data_list[0]
        image_bytes = base64.b64decode(image_base64)
        return image_bytes


class ImageOptimizationService:
    @staticmethod
    def optimize_for_web(image_bytes: bytes, quality: int = 80) -> bytes:
        """
        Optimizes an image by converting it to WebP format.
        Keeps the image size small (typically < 200KB for 1024x1024 at quality=80).
        """
        logger.info("Optimizing image to WebP format...")
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
            
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='WEBP', quality=quality)
        return img_byte_arr.getvalue()
