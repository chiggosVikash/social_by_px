from PIL import Image, ImageDraw, ImageFont
import io

def generate_slide_image(text: str, bg_color: tuple = (255, 255, 255), text_color: tuple = (0, 0, 0)) -> bytes:
    """Generates a simple 1080x1080 slide image for social media carousels."""
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # We use a default font since we don't have custom fonts loaded yet
    # In production, we'd load an actual .ttf file
    font = ImageFont.load_default()
    
    # Basic text wrapping logic
    lines = []
    # VERY naive wrapping for stub purposes
    words = text.split()
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 30: # arbitrary wrap limit
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    y_text = height / 2 - (len(lines) * 40) / 2
    for line in lines:
        # Use simple textbox bounding box approximation
        # Normally would use draw.textbbox
        draw.text((width/2 - 200, y_text), line, font=font, fill=text_color)
        y_text += 40
        
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
