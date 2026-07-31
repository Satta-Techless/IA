import os
import json
import datetime
from PIL import ImageDraw, ImageFont

def load_json(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath: str, data: dict):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_today_str() -> str:
    return datetime.datetime.now().strftime('%Y%m%d')

def wrap_text(draw: ImageDraw, text: str, font: ImageFont, max_width: int) -> list:
    """Wrap text to fit within a given pixel width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

FONT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLD_FONT = os.path.join(FONT_DIR, "Inter-Bold.ttf")
REGULAR_FONT = os.path.join(FONT_DIR, "Inter-Regular.ttf")

def get_font(weight='bold', size=40):
    font_path = BOLD_FONT if weight == 'bold' else REGULAR_FONT
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()