import os
import json
import datetime
from .orchestrator import Orchestrator
from .utils import load_json

class DeepDiveGenerator:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.colors = load_json('color_palette.json')

    async def generate_section_image(self, section_title: str, subcategory: str, trigger: str, colors: dict) -> str:
        prompt = f"Banner 1200x600 for section: '{section_title}'. Topic: {subcategory}. Trigger: {trigger}. Colors: {colors.get('primary')} and {colors.get('secondary')}. Magazine style, photorealistic, no text."
        image_data = await self.orchestrator.gemini_generate_image(prompt)
        if image_data:
            os.makedirs("deep_dive_images", exist_ok=True)
            filename = f"deep_dive_images/{subcategory}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(image_data)
            return filename
        return None

    async def generate_article(self, subcategory: str, week_articles: list, dominant_trigger: str, colors: dict) -> dict:
        articles_text = "\n\n".join([f"Title: {a['title']}\nSummary: {a.get('text', '')[:300]}..." for a in week_articles[:30]])
        prompt = f"""
        Write a 2000-word deep-dive on "{subcategory}". Dominant trigger: {dominant_trigger}.
        Top 30 headlines: {articles_text}
        Structure: TITLE, INTRO (150 words), 3-5 SECTIONS (headings + 300 words each), CONCLUSION (150 words), SOURCES.
        Return JSON: {{"title": "...", "intro": "...", "sections": [{{"heading": "...", "content": "..."}}], "conclusion": "...", "sources": ["..."]}}
        """
        result = await self.orchestrator.groq_completion(prompt, temperature=0.8, response_format={"type": "json_object"})
        article_data = json.loads(result)

        section_images = []
        for idx, section in enumerate(article_data['sections'][:5]):
            img_path = await self.generate_section_image(section['heading'], subcategory, dominant_trigger, colors)
            if img_path:
                section_images.append({"heading": section['heading'], "image_path": img_path})

        final = {
            "subcategory": subcategory,
            "date": datetime.datetime.now().isoformat(),
            "dominant_trigger": dominant_trigger,
            "title": article_data['title'],
            "intro": article_data['intro'],
            "sections": article_data['sections'],
            "conclusion": article_data['conclusion'],
            "section_images": section_images,
            "sources": article_data.get('sources', []),
            "color_palette": colors
        }
        os.makedirs("deep_dive_articles", exist_ok=True)
        filename = f"deep_dive_articles/{subcategory}_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(final, f, indent=2)
        return final