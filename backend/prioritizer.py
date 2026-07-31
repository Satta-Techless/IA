import os
import json
import statistics
from datetime import datetime, timedelta
from .utils import load_json

class WeeklyPrioritizer:
    def __init__(self):
        self.ontology = load_json('ontology.json')
        self.trigger_matrix = self.ontology['subcategory_trigger_matrix']

    def load_7_day_data(self) -> dict:
        weekly = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            fname = f'daily_results_{date}.json'
            if os.path.exists(fname):
                with open(fname, 'r') as f:
                    data = json.load(f)
                    for cat in data:
                        for subcat, results in data[cat].items():
                            if subcat not in weekly:
                                weekly[subcat] = []
                            weekly[subcat].extend(results.get('top_5_articles', []))
        return weekly

    def calculate_deep_dive_score(self, subcategory: str, week_articles: list) -> dict:
        if not week_articles:
            return {"score": 0, "avg_net": 0, "high_count": 0, "trigger_variance": 0}
        net_scores = [a.get('net_score', 0) for a in week_articles]
        avg_net = statistics.mean(net_scores) if net_scores else 0
        high_count = sum(1 for s in net_scores if s > 0.6)
        triggers = [a.get('primary_trigger', 'neutral') for a in week_articles]
        freq = {}
        for t in triggers:
            freq[t] = freq.get(t, 0) + 1
        trigger_variance = len(freq) / len(triggers) if triggers else 0
        deep_dive_score = (avg_net * 0.5) + (high_count * 0.3) + (trigger_variance * 0.2)
        return {
            "score": round(deep_dive_score, 4),
            "avg_net": round(avg_net, 3),
            "high_count": high_count,
            "trigger_variance": round(trigger_variance, 3),
            "dominant_trigger": max(freq, key=freq.get) if freq else "curiosity"
        }

    def select_subcategory_of_the_week(self) -> dict:
        week_data = self.load_7_day_data()
        best = None
        best_score = -1
        for subcat, articles in week_data.items():
            if len(articles) < 10:
                continue
            result = self.calculate_deep_dive_score(subcat, articles)
            if result['score'] > best_score:
                best_score = result['score']
                best = {
                    "subcategory": subcat,
                    "score": result['score'],
                    "dominant_trigger": result['dominant_trigger'],
                    "avg_net": result['avg_net'],
                    "article_count": len(articles)
                }
        return best