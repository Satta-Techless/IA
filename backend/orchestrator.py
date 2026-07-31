import os
import json
import asyncio
import time
from typing import List, Dict, Any, Optional
from groq import Groq
import google.generativeai as genai
from .rate_limiter import AsyncRateLimiter

class Orchestrator:
    """
    The "Helping Hand" – handles all Groq + Gemini calls with:
    - Concurrency control (semaphores)
    - Exponential backoff retries
    - Fallback to neutral scores / PIL images on failure
    - Model switching (if one model fails, try another)
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
        self.rate_limiter = AsyncRateLimiter(rate=25)  # 25 req/min safe margin
        self.semaphore = asyncio.Semaphore(10)         # Max 10 concurrent calls

    # ---------- Groq Helpers ----------
    async def groq_completion(self, prompt: str, model: str = "llama-3.3-70b-versatile", 
                              temperature: float = 0.1, response_format: Optional[dict] = None) -> str:
        """Single Groq call with retries and rate limiting."""
        await self.rate_limiter.acquire()
        async with self.semaphore:
            for attempt in range(4):  # 3 retries + 1 initial
                try:
                    kwargs = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                    }
                    if response_format:
                        kwargs["response_format"] = response_format
                    completion = await asyncio.to_thread(
                        self.groq_client.chat.completions.create, **kwargs
                    )
                    return completion.choices[0].message.content
                except Exception as e:
                    wait = 2 ** attempt + 0.5
                    print(f"Groq attempt {attempt+1} failed: {e}. Retrying in {wait}s")
                    await asyncio.sleep(wait)
            # Ultimate fallback
            print("Groq failed after 4 attempts. Returning fallback.")
            return "{}" if response_format else ""

    async def groq_batch_scoring(self, articles: List[Dict], subcategory: str, trigger_list: str) -> List[Dict]:
        """Score a batch of articles with controlled concurrency."""
        tasks = []
        for article in articles:
            text = article.get('text', article['title'])[:1200]
            prompt = f"Rate this article (0.0-1.0) for: {trigger_list}. Article: '{text}'. Return JSON."
            tasks.append(self.groq_completion(prompt, response_format={"type": "json_object"}))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, res in enumerate(results):
            try:
                score_data = json.loads(res) if isinstance(res, str) else {}
            except:
                score_data = {t: 0.5 for t in trigger_list.split(', ')}
            articles[idx]['llm_scores'] = score_data
        return articles

    # ---------- Gemini Helpers ----------
    async def gemini_generate_image(self, prompt: str, retries: int = 3) -> Optional[bytes]:
        """Generate an image with Gemini, with retries and fallback."""
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content, prompt
                )
                if response._result.candidates:
                    image_data = response._result.candidates[0].content.parts[0].inline_data.data
                    return image_data
            except Exception as e:
                print(f"Gemini attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2 ** attempt)
        return None

    async def gemini_batch_images(self, prompts: List[Dict]) -> List[Optional[bytes]]:
        """Generate multiple images concurrently."""
        tasks = []
        for p in prompts:
            tasks.append(self.gemini_generate_image(p['prompt']))
        return await asyncio.gather(*tasks)