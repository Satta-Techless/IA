import os
import json
from typing import Dict, List
from .orchestrator import Orchestrator
from .utils import load_json

class OntologyScorer:
    def __init__(self):
        self.ontology = load_json('ontology.json')
        self.colors = load_json('color_palette.json')
        self.trigger_matrix = self.ontology['subcategory_trigger_matrix']
        self.orchestrator = Orchestrator()

    async def score_articles_batch(self, articles: List[Dict], subcategory: str) -> List[Dict]:
        sub_data = self.trigger_matrix.get(subcategory, {})
        base_triggers = sub_data.get('triggers', {})
        base_brakes = sub_data.get('brakes', {})
        if not base_triggers:
            for a in articles:
                a.update({"net_score": 0.0, "primary_trigger": "none"})
            return articles

        trigger_list = ", ".join(base_triggers.keys())
        # Get LLM scores via orchestrator
        scored_articles = await self.orchestrator.groq_batch_scoring(articles, subcategory, trigger_list)
        
        for article in scored_articles:
            llm_scores = article.get('llm_scores', {})
            final_scores = {}
            for t_id, base_weight in base_triggers.items():
                llm_score = llm_scores.get(t_id, 0.5)
                final_scores[t_id] = (base_weight + llm_score) / 2.0

            avg_brake = sum(base_brakes.values()) / len(base_brakes) if base_brakes else 0.0
            trigger_sum = sum(final_scores.values())
            brake_reduction = avg_brake * 0.5
            net_score = (trigger_sum * (1 - brake_reduction)) - (avg_brake * 0.3)
            primary = max(final_scores, key=final_scores.get)
            visual = self.colors.get(subcategory, {})
            article.update({
                "net_score": round(net_score, 4),
                "primary_trigger": primary,
                "color_palette": visual,
                "brake_penalty": round(avg_brake, 3),
                "action": "PUBLISH" if net_score > 0.45 else "REJECT"
            })
            # Clean up temporary field
            if 'llm_scores' in article:
                del article['llm_scores']
        return scored_articles