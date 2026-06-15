import base64
import io
import logging
from typing import Optional
from abc import ABC, abstractmethod
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
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


# [PATTERN: Strategy] - Strategy interface for slide image generation
class SlideImageGenerationStrategy(ABC):
    @abstractmethod
    async def generate_and_save(
        self,
        db: AsyncSession,
        slide,
        article,
        project,
        idx: int,
        total: int
    ) -> Optional[str]:
        """Generate a slide image, upload it to storage, and return the permanent URL."""
        pass


# [SOLID: OCP] - Concrete Strategy for AI DALL-E Image Generation
class DalleSlideImageStrategy(SlideImageGenerationStrategy):
    async def generate_and_save(
        self,
        db: AsyncSession,
        slide,
        article,
        project,
        idx: int,
        total: int
    ) -> Optional[str]:
        import uuid
        from services.style_presets import get_preset
        from services.renderer import composite_text_on_background
        from services.storage import upload_file

        preset = get_preset(getattr(project, "style_preset", None))

        dalle_prompt = (
            f"{slide.image_prompt}\n\n"
            f"FORMAT: 1080x1080 square, social media carousel slide background.\n"
            f"STYLE LOCK: {preset.style}\n"
            f"COLOR PALETTE (use ONLY these, with at most 20% accent): "
            f"{', '.join(preset.palette)}\n"
            f"LEAVE A CLEAR {slide.text_zone.upper()} zone empty for text overlay.\n"
            f"DO NOT include any text, letters, words, or typography in the image.\n"
            f"NO faces, no people, no stock photos, no neon gradients, "
            f"no glossy AI-render look, no busy collages."
        )

        image_service = get_image_generation_service()
        raw_image_bytes = await image_service.generate(dalle_prompt)
        if not raw_image_bytes:
            return None

        rendered_bytes = await composite_text_on_background(
            text_content=slide.text_content or "",
            emoji=slide.emoji,
            caption=slide.caption,
            background_url=None,
            background_bytes=raw_image_bytes,
            text_zone=slide.text_zone,
            slide_index=idx,
            total_slides=total,
        )

        optimized_bytes = ImageOptimizationService.optimize_for_web(rendered_bytes, quality=85)
        file_name = f"slides/article_{article.id}_slide_{idx}_{uuid.uuid4().hex[:8]}.webp"
        return await upload_file(optimized_bytes, file_name, content_type="image/webp")


# [SOLID: OCP] - Concrete Strategy for Local PIL Text Compositing
class TemplateCompositingSlideImageStrategy(SlideImageGenerationStrategy):
    async def generate_and_save(
        self,
        db: AsyncSession,
        slide,
        article,
        project,
        idx: int,
        total: int
    ) -> Optional[str]:
        import uuid
        from services.renderer import composite_text_on_background
        from services.storage import upload_file

        if not project.background_image_url:
            raise ValueError("No background image template uploaded for project.")

        rendered_bytes = await composite_text_on_background(
            text_content=slide.text_content or "",
            emoji=slide.emoji,
            caption=slide.caption,
            background_url=project.background_image_url,
            text_zone=slide.text_zone or "center-bottom third",
            slide_index=idx,
            total_slides=total
        )

        file_name = f"slides/article_{article.id}_slide_{idx}_{uuid.uuid4().hex[:8]}.webp"
        return await upload_file(rendered_bytes, file_name, content_type="image/webp")


# [SOLID: OCP] - Concrete Strategy for Programmatic PIL Background (minimalist)
class ProgrammaticPILStrategy(SlideImageGenerationStrategy):
    """Minimal PIL gradient for 'minimalist' slides. Full implementation in the spec."""
    async def generate_and_save(
        self,
        db: AsyncSession,
        slide,
        article,
        project,
        idx: int,
        total: int,
    ) -> Optional[str]:
        import uuid
        from services.renderer import composite_text_on_background
        from services.storage import upload_file
        from PIL import Image as PILImage, ImageDraw

        # Create a simple gradient background
        img = PILImage.new("RGB", (1080, 1080), color=(245, 241, 232))  # cream
        draw = ImageDraw.Draw(img)
        # Simple gradient from cream to charcoal
        for y in range(1080):
            r = int(245 - (y / 1080) * (245 - 45))
            g = int(241 - (y / 1080) * (241 - 45))
            b = int(232 - (y / 1080) * (232 - 45))
            draw.line([(0, y), (1080, y)], fill=(r, g, b))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        background_bytes = buf.getvalue()

        rendered_bytes = await composite_text_on_background(
            text_content=slide.text_content or "",
            emoji=slide.emoji,
            caption=slide.caption,
            background_url=None,
            background_bytes=background_bytes,
            text_zone=slide.text_zone,
            slide_index=idx,
            total_slides=total,
        )
        file_name = f"slides/article_{article.id}_slide_{idx}_{uuid.uuid4().hex[:8]}.webp"
        return await upload_file(rendered_bytes, file_name, content_type="image/webp")


# [PATTERN: Factory] - Factory to resolve slide image generation strategy
class SlideImageStrategyFactory:
    _ROUTES = {
        "minimalist": ProgrammaticPILStrategy,
        "thematic": TemplateCompositingSlideImageStrategy,
        "generative": DalleSlideImageStrategy,
    }

    @staticmethod
    def get_strategy(visual_type: str) -> SlideImageGenerationStrategy:
        impl = SlideImageStrategyFactory._ROUTES.get(visual_type)
        if impl is None:
            raise ValueError(f"Unknown visual_type: {visual_type!r}")
        return impl()
