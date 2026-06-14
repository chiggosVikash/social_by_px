import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
import httpx
from typing import Optional
from services.font import FontService

logger = logging.getLogger(__name__)

async def generate_slide_image(text: str, bg_color: tuple = (255, 255, 255), text_color: tuple = (0, 0, 0)) -> bytes:
    """Generates a simple 1080x1080 slide image for social media carousels asynchronously."""
    def _generate():
        width, height = 1080, 1080
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        font = ImageFont.load_default()
        
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 30:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))
            
        y_text = height / 2 - (len(lines) * 40) / 2
        for line in lines:
            draw.text((width/2 - 200, y_text), line, font=font, fill=text_color)
            y_text += 40
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
        
    return await asyncio.to_thread(_generate)

# [SOLID: SRP] - Component responsible only for rendering text content over image templates
async def composite_text_on_background(
    text_content: str,
    emoji: Optional[str],
    caption: Optional[str],
    background_url: Optional[str],
    slide_index: int,
    total_slides: int
) -> bytes:
    """
    Renders slide text, caption, emoji, and slide counter onto a background image template.
    Returns optimized WebP bytes.
    """
    if not background_url:
        raise ValueError("Background image URL is required for template compositing.")
        
    def _render():
        # 1. Load the background image
        img = None
        
        # Check if local development URL
        if "localhost:8000/static/" in background_url:
            file_name = background_url.split("/static/")[-1]
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static"))
            local_path = os.path.join(static_dir, file_name)
            if os.path.exists(local_path):
                try:
                    img = Image.open(local_path)
                    img.load()  # Force load
                except Exception as e:
                    logger.error(f"Failed to open local background image: {e}")
                    
        # [SOLID: DIP] — bypassed unauthenticated HTTP GET in favor of authenticated S3 client for R2 URLs
        from core.config import get_settings
        settings = get_settings()
        is_r2_url = False
        bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
        key = None
        
        if settings.CLOUDFLARE_R2_ENDPOINT_URL:
            endpoint = settings.CLOUDFLARE_R2_ENDPOINT_URL.rstrip("/")
            if background_url.startswith(endpoint):
                is_r2_url = True
                rel_path = background_url[len(endpoint):].lstrip("/")
                path_parts = rel_path.split("/", 1)
                if len(path_parts) == 2:
                    bucket_name, key = path_parts
                    
        if not is_r2_url and settings.CLOUDFLARE_R2_PUBLIC_URL:
            public_url = settings.CLOUDFLARE_R2_PUBLIC_URL.rstrip("/")
            if background_url.startswith(public_url):
                is_r2_url = True
                key = background_url[len(public_url):].lstrip("/")
                
        if img is None and is_r2_url and key:
            try:
                logger.info(f"Downloading background template directly from S3/R2. Bucket: {bucket_name}, Key: {key}")
                from services.storage import get_s3_client
                s3_client = get_s3_client(settings)
                if s3_client:
                    resp = s3_client.get_object(Bucket=bucket_name, Key=key)
                    img = Image.open(io.BytesIO(resp['Body'].read()))
                    img.load()
            except Exception as e:
                logger.error(f"Failed to load background template from R2 directly: {e}")
                    
        if img is None:
            # Download remote image
            try:
                resp = httpx.get(background_url, timeout=15.0)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img.load()
            except Exception as e:
                logger.error(f"Failed to download remote background image {background_url}: {e}")
                raise RuntimeError(f"Could not load background image: {e}")

        # 2. Resize and crop background to exactly 1080x1080
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        
        img = img.crop((left, top, right, bottom))
        img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        
        # 3. Create semi-transparent overlay to ensure text is readable
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 115))  # ~45% opacity black overlay
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        
        draw = ImageDraw.Draw(img)
        
        # 4. Resolve Fonts
        font_emoji = FontService.get_font("Bold", 72)
        font_main = FontService.get_font("Bold", 46)
        font_caption = FontService.get_font("Regular", 28)
        font_counter = FontService.get_font("Bold", 24)
        
        # 5. Draw Slide Counter (e.g. "1 / 5") in the bottom-right corner
        counter_str = f"{slide_index + 1} / {total_slides}"
        counter_bbox = draw.textbbox((0, 0), counter_str, font=font_counter)
        counter_w = counter_bbox[2] - counter_bbox[0]
        counter_h = counter_bbox[3] - counter_bbox[1]
        draw.text((1080 - counter_w - 60, 1080 - counter_h - 60), counter_str, font=font_counter, fill=(200, 200, 200))
        
        # Helper to wrap and draw centered text
        def draw_centered_text(text_str, font_obj, fill_color, max_width, start_y, line_height_mult=1.4):
            words = text_str.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                test_str = " ".join(current_line)
                bbox = draw.textbbox((0, 0), test_str, font=font_obj)
                w = bbox[2] - bbox[0]
                if w > max_width:
                    if len(current_line) > 1:
                        current_line.pop()
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        lines.append(test_str)
                        current_line = []
            if current_line:
                lines.append(" ".join(current_line))
                
            y = start_y
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_obj)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                x = (1080 - w) / 2
                draw.text((x, y), line, font=font_obj, fill=fill_color)
                y += int(h * line_height_mult)
            return y
            
        # 6. Draw Emoji (top center)
        current_y = 250
        if emoji:
            emoji_bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
            emoji_w = emoji_bbox[2] - emoji_bbox[0]
            draw.text(((1080 - emoji_w)/2, current_y), emoji, font=font_emoji, fill=(255, 255, 255))
            current_y += 120
            
        # 7. Draw Main Text Content (centered)
        text_content_clean = text_content.strip()
        current_y = draw_centered_text(text_content_clean, font_main, (255, 255, 255), 900, current_y)
        
        # 8. Draw Caption (if present)
        if caption:
            current_y += 40
            draw_centered_text(caption.strip(), font_caption, (200, 200, 200), 800, current_y)
            
        # 9. Save as WebP
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='WEBP', quality=85)
        return img_byte_arr.getvalue()
        
    return await asyncio.to_thread(_render)
