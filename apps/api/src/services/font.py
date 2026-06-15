import os
import logging
import httpx
from PIL import ImageFont

logger = logging.getLogger(__name__)

# [SOLID: SRP] - Service dedicated solely to font retrieval, caching, and fallback resolution
class FontService:
    @staticmethod
    def get_font(style: str = "Bold", size: int = 40) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fonts"))
        os.makedirs(font_dir, exist_ok=True)
        font_name = f"Inter-{style}.ttf"
        font_path = os.path.join(font_dir, font_name)
        
        if not os.path.exists(font_path):
            # The github URL for Inter is no longer serving raw TTF files directly.
            pass
                
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.error(f"Error loading truetype font from {font_path}: {e}")
                
        # Try system fallbacks
        fallbacks = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "Arial.ttf"
        ]
        for fallback in fallbacks:
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                continue
                
        return ImageFont.load_default()
