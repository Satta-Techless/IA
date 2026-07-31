import os
import json
import asyncio
import datetime
from .scraper import WideScopeScraper
from .scorer import OntologyScorer
from .generator import A4PosterGenerator
from .prioritizer import WeeklyPrioritizer
from .deep_dive_generator import DeepDiveGenerator
from .utils import load_json, save_json, get_today_str
from .cache import mark_url_processed

async def run_daily_pipeline():
    print("🚀 Starting Daily Pipeline...")
    ontology = load_json('ontology.json')
    scraper = WideScopeScraper()
    scorer = OntologyScorer()
    poster_gen = A4PosterGenerator()

    all_results = {}
    categories = ontology['categories']

    for category in categories:
        cat_id = category['id']
        all_results[cat_id] = {}
        for subcat in category['subcategories']:
            print(f"Processing {cat_id} → {subcat}")
            if cat_id == 'history':
                hist_data = await scraper.fetch_history_events()
                articles = [{"title": e, "text": e, "source": "Wikipedia"} for e in hist_data.get(subcat, [])]
            else:
                articles = scraper.fetch_articles(subcat, limit=150)

            if not articles:
                all_results[cat_id][subcat] = {"top_5_articles": [], "poster": None}
                continue

            # Score asynchronously
            scored = await scorer.score_articles_batch(articles, subcat)
            scored.sort(key=lambda x: x.get('net_score', 0), reverse=True)
            top_5 = scored[:5]

            if top_5:
                primary = top_5[0].get('primary_trigger', 'curiosity')
                colors = top_5[0].get('color_palette', {})
                poster_path = await poster_gen.generate_poster(subcat, top_5, colors, primary)
                for a in top_5:
                    mark_url_processed(a['url'], a['title'], subcat, poster_path)
            else:
                poster_path = None

            all_results[cat_id][subcat] = {
                "top_5_articles": top_5,
                "poster": poster_path,
                "timestamp": datetime.datetime.now().isoformat()
            }

    today = get_today_str()
    save_json(f'daily_results_{today}.json', all_results)
    save_json('daily_results_latest.json', all_results)
    print("✅ Daily pipeline complete.")

async def run_weekly_deep_dive():
    print("🔍 Weekly Deep Dive Analysis Starting...")
    prioritizer = WeeklyPrioritizer()
    winner = prioritizer.select_subcategory_of_the_week()
    if not winner:
        print("⚠️ No subcategory qualified.")
        return
    print(f"🏆 Subcategory of the Week: {winner['subcategory']}")

    week_data = prioritizer.load_7_day_data()
    articles = week_data.get(winner['subcategory'], [])
    if len(articles) < 10:
        return

    deep_gen = DeepDiveGenerator()
    colors = deep_gen.colors.get(winner['subcategory'], {})
    article = await deep_gen.generate_article(
        subcategory=winner['subcategory'],
        week_articles=articles,
        dominant_trigger=winner['dominant_trigger'],
        colors=colors
    )
    latest = load_json('daily_results_latest.json')
    latest['deep_dive_article'] = {
        "subcategory": winner['subcategory'],
        "url": f"deep_dive_articles/{winner['subcategory']}_{datetime.datetime.now().strftime('%Y%m%d')}.json",
        "title": article['title']
    }
    save_json('daily_results_latest.json', latest)
    print(f"📄 Deep Dive generated: {article['title']}")