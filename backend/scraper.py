import datetime
import json
import time
import requests
import feedparser
from urllib.parse import parse_qs, unquote, urlparse
from newspaper import Article as NewspaperArticle
from typing import List, Dict
from .cache import is_url_processed
from .orchestrator import Orchestrator

PAYWALLED_DOMAINS = ['nytimes.com', 'wsj.com', 'bloomberg.com', 'ft.com', 'reuters.com']

class WideScopeScraper:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.query_map = {
            "global": "global economy world news",
            "finance": "stock market finance banking",
            "tech": "technology innovation AI startups",
            "energy": "renewable energy oil gas sustainability",
            "north_america": "US Canada Mexico business trade",
            "europe": "European Union UK Germany France economy",
            "asia_pacific": "China Japan India Australia business",
            "africa": "South Africa Nigeria Kenya African economy",
            "mathematics": "mathematics research breakthrough theorem",
            "business_economics": "economics research business strategy",
            "social_science": "sociology psychology anthropology research",
            "natural_science": "nature biology environment research",
            "physical_science": "physics chemistry astronomy quantum",
            "life_sciences": "genetics medicine biotechnology life sciences",
            "health": "public health medical breakthrough wellness",
            "humanities": "philosophy history literature arts research",
            "business_history": "historical business events corporate history",
            "invention_history": "historical inventions technology history",
            "ideas_history": "historical philosophy great ideas"
        }

    def _clean_google_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc == "news.google.com":
            query_params = parse_qs(parsed.query)
            for key in ("url", "q"):
                candidate = query_params.get(key, [None])[0]
                if not candidate:
                    continue
                decoded = unquote(candidate).strip()
                parsed_candidate = urlparse(decoded)
                if parsed_candidate.scheme in {"http", "https"} and parsed_candidate.netloc:
                    return decoded
        return url
 
    def _is_paywalled(self, url: str) -> bool:
        hostname = urlparse(url).hostname or ""
        return any(hostname == d or hostname.endswith(f".{d}") for d in PAYWALLED_DOMAINS)

    def fetch_articles(self, subcategory: str, limit: int = 150) -> List[Dict]:
        query = self.query_map.get(subcategory, subcategory.replace('_', ' '))
        query_encoded = '+'.join(query.split())
        rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-US&gl=US&ceid=US:en"
        print(f"🌐 Fetching {subcategory}...")
        try:
            feed = feedparser.parse(rss_url)
            articles = []
            for entry in feed.entries[:limit]:
                real_url = self._clean_google_url(entry.link)
                if is_url_processed(real_url):
                    continue
                if self._is_paywalled(real_url):
                    text = entry.get('summary', entry.title)
                    source = "PaywallFallback"
                else:
                    try:
                        article = NewspaperArticle(real_url)
                        article.download()
                        article.parse()
                        text = article.text[:2000] if article.text else entry.get('summary', '')
                        title = article.title or entry.title
                        source = "Newspaper3k"
                    except Exception:
                        text = entry.get('summary', entry.title)
                        title = entry.title
                        source = "Fallback"
                articles.append({
                    "title": title if 'title' in locals() else entry.title,
                    "url": real_url,
                    "published": entry.get('published', ''),
                    "source": source,
                    "subcategory": subcategory,
                    "text": text
                })
                time.sleep(0.3)
            print(f"✅ Fetched {len(articles)} new articles for {subcategory}")
            return articles
        except Exception as e:
            print(f"❌ Failed for {subcategory}: {e}")
            return []

    async def fetch_history_events(self) -> Dict[str, List[Dict]]:
        today = datetime.datetime.now()
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
        resp = requests.get(url)
        data = resp.json()
        events = []
        for event in data.get("events", [])[:50]:
            events.append({"text": event.get("text", ""), "year": event.get("year", "")})
        # Use Groq to categorize (Patch 6)
        prompt = f"""
        Categorize these historical events into exactly 3 buckets: 
        'business_history', 'invention_history', 'ideas_history'.
        Return JSON with three keys, each containing a list of the full event strings.
        Events: {json.dumps(events)}
        """
        result = await self.orchestrator.groq_completion(prompt, response_format={"type": "json_object"})
        try:
            return json.loads(result)
        except:
            # Fallback to keyword matching
            categorized = {"business_history": [], "invention_history": [], "ideas_history": []}
            for e in events:
                text = e['text'].lower()
                if any(w in text for w in ["company", "bank", "trade", "market", "stock"]):
                    categorized["business_history"].append(f"{e['year']}: {e['text']}")
                elif any(w in text for w in ["invent", "patent", "device", "machine", "discover"]):
                    categorized["invention_history"].append(f"{e['year']}: {e['text']}")
                else:
                    categorized["ideas_history"].append(f"{e['year']}: {e['text']}")
            return categorized