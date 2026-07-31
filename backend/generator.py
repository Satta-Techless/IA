import os
import json
import datetime
import hashlib
import io
from PIL import Image, ImageDraw
from .orchestrator import Orchestrator
from .utils import get_font, wrap_text, load_json
from .cache import is_image_cached, save_image_cache, get_image_cache_path

class A4PosterGenerator:
    def __init__(self):
        self.WIDTH = 2480
        self.HEIGHT = 3508
        self.MARGIN = 80
        self.ROW_HEIGHT = 500
        self.IMG_WIDTH = 420
        self.IMG_HEIGHT = 280
        self.orchestrator = Orchestrator()
        self.colors = load_json('color_palette.json')

    async def _generate_article_image(self, title: str, trigger: str, colors: dict, subcategory: str) -> Image.Image:
        cache_key = hashlib.md5(f"{title}_{subcategory}_{trigger}".encode()).hexdigest()
        if is_image_cached(cache_key):
            return Image.open(get_image_cache_path(cache_key))
        
        prompt = f"""
        Generate a professional, magazine-style thumbnail (420x280) for this article.
        Title: "{title}". Category: {subcategory}. Trigger: {trigger}.
        Colors: {colors.get('primary', '#1A1A2E')} and {colors.get('secondary', '#E94560')}.
        Photorealistic, business publication style. No text overlay.
        """
        image_data = await self.orchestrator.gemini_generate_image(prompt)
        if image_data:
            img = Image.open(io.BytesIO(image_data)).resize((self.IMG_WIDTH, self.IMG_HEIGHT))
            save_image_cache(cache_key, image_data)
            return img
        else:
            # PIL Fallback
            img = Image.new('RGB', (self.IMG_WIDTH, self.IMG_HEIGHT), colors.get('primary', '#2D2D2D'))
            draw = ImageDraw.Draw(img)
            font = get_font('bold', 24)
            draw.text((20, 120), f"TRIGGER: {trigger.upper()}", fill=colors.get('secondary', '#FFFFFF'), font=font)
            return img

    async def _generate_poster_copy(self, subcategory: str, top_5: list, primary_trigger: str) -> dict:
        articles_text = "\n".join([f"- {a['title']}" for a in top_5])
        prompt = f"""
        Write a magazine-style "Top 5" summary for LinkedIn professionals.
        Category: {subcategory}. Primary Trigger: {primary_trigger}.
        Articles: {articles_text}
        Generate: a powerful TITLE (max 8 words), a SUBHEADLINE (max 15 words), and 5 "WHY IT MATTERS" blurbs (max 25 words each).
        Return JSON: {{"title": "...", "subtitle": "...", "summaries": ["blurb1", ...]}}
        """
        result = await self.orchestrator.groq_completion(prompt, response_format={"type": "json_object"})
        return json.loads(result)

    async def generate_poster(self, subcategory: str, top_5: list, colors: dict, primary_trigger: str) -> str:
        copy = await self._generate_poster_copy(subcategory, top_5, primary_trigger)
        bg = Image.new('RGB', (self.WIDTH, self.HEIGHT), colors.get('primary', '#0A0A0A'))
        draw = ImageDraw.Draw(bg)

        title_font = get_font('bold', 140)
        subtitle_font = get_font('regular', 70)
        heading_font = get_font('bold', 55)
        body_font = get_font('regular', 40)

        x, y = self.MARGIN, self.MARGIN
        draw.text((x, y), copy['title'], font=title_font, fill="#FFFFFF")
        y += 160
        draw.text((x, y), copy['subtitle'], font=subtitle_font, fill="#CCCCCC")
        y += 120
        draw.line([(x, y), (self.WIDTH - self.MARGIN, y)], fill=colors.get('secondary', '#E94560'), width=10)
        y += 80

        for idx, article in enumerate(top_5):
            trigger = article.get('primary_trigger', 'curiosity')
            img = await self._generate_article_image(article['title'], trigger, colors, subcategory)
            bg.paste(img, (x, y))
            text_x = x + self.IMG_WIDTH + 40
            text_y = y + 20
            title_lines = wrap_text(draw, f"{idx+1}. {article['title']}", heading_font, 800)
            for line in title_lines:
                draw.text((text_x, text_y), line, font=heading_font, fill="#FFFFFF")
                text_y += 70
            blurb = copy['summaries'][idx]
            blurb_lines = wrap_text(draw, f"WHY IT MATTERS: {blurb}", body_font, 800)
            for line in blurb_lines:
                draw.text((text_x, text_y), line, font=body_font, fill="#D3D3D3")
                text_y += 50
            y += self.ROW_HEIGHT
            if idx < 4:
                draw.line([(x, y), (self.WIDTH - self.MARGIN, y)], fill="#333333", width=3)
                y += 40

        y = self.HEIGHT - 120
        sources = ", ".join([a.get('source', 'News') for a in top_5])
        draw.text((x, y), f"SOURCES: {sources} | Visuals governed by {primary_trigger.upper()}", font=body_font, fill="#888888")

        os.makedirs("posters", exist_ok=True)
        filename = f"posters/{subcategory}_A4_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.png"
        bg.save(filename, "PNG", dpi=(300, 300))
        return filename