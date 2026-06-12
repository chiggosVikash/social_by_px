import base64
import io
import logging
from typing import Optional
from abc import ABC, abstractmethod
from PIL import Image
from openai import AsyncOpenAI
from core.config import get_settings

logger = logging.getLogger(__name__)

# [PATTERN: Strategy] - Abstract base class for image generation
class ImageGenerationStrategy(ABC):
    @abstractmethod
    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """Generate an image from a prompt and return the raw bytes."""
        pass


# [SOLID: OCP] - Concrete Strategy for OpenAI DALL-E
class OpenAIImageStrategy(ImageGenerationStrategy):
    async def generate_image(self, prompt: str) -> Optional[bytes]:
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
            logger.error(f"Failed to generate image with OpenAI: {api_e}")
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
        return base64.b64decode(image_base64)


# [SOLID: OCP] - Example placeholder for future OpenRouter Strategy
class OpenRouterImageStrategy(ImageGenerationStrategy):
    async def generate_image(self, prompt: str) -> Optional[bytes]:
        # TODO: Implement OpenRouter / DeepSeek logic here in the future
        logger.info("OpenRouter strategy called but not yet implemented.")
        raise NotImplementedError("OpenRouter integration coming soon")


# [SOLID: DIP] - Service depends on abstraction
class ImageGenerationService:
    """
    Context class that uses an injected ImageGenerationStrategy to generate images.
    """
    def __init__(self, strategy: ImageGenerationStrategy):
        self._strategy = strategy

    async def generate(self, prompt: str) -> Optional[bytes]:
        return await self._strategy.generate_image(prompt)


# [PATTERN: Factory] - Centralized instantiation
def get_image_generation_service() -> ImageGenerationService:
    """
    Factory to resolve the correct strategy. 
    In the future, you can read from `get_settings().IMAGE_PROVIDER` to choose between OpenAI, OpenRouter, etc.
    """
    strategy = OpenAIImageStrategy()
    return ImageGenerationService(strategy)


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
