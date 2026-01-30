from sqlalchemy.orm import Session
from app.models import ContentItem, SourceType
from sqlalchemy import func
from datetime import datetime, timedelta
import re

class ContentRanker:
    def __init__(self, db: Session):
        self.db = db

    def calculate_final_scores(self, lookback_hours=24):
        """
        Calculates and updates final_score for items ingested within lookback_hours.
        """
        since = datetime.now() - timedelta(hours=lookback_hours)
        items = self.db.query(ContentItem).filter(ContentItem.timestamp >= since).all()
        
        if not items:
            return

        # 1. Calculate Coverage Signals
        # Group items by title similarity (naive approach: fuzzy match or title words)
        coverage_counts = self._calculate_coverage_signals(items)

        # 2. Get Max Engagement for Normalization
        max_engagement = self._get_max_engagement(items)

        for item in items:
            score = 0.0
            
            # Factor 1: Controversy Score (40%)
            score += (item.controversy_score or 0.0) * 0.4

            # Factor 2: Engagement (30%)
            engagement_signal = self._calculate_engagement_signal(item, max_engagement)
            score += engagement_signal * 0.3

            # Factor 3: Coverage (30%)
            coverage_signal = self._calculate_coverage_signal(item, coverage_counts)
            score += coverage_signal * 0.3

            item.final_score = round(min(score, 1.0), 3)
        
        self.db.commit()

    def _calculate_coverage_signals(self, items):
        """
        Naively counts occurrences of similar titles across different sources.
        """
        counts = {}
        for item in items:
            # Simple normalization: lowercase and remove non-alphanumeric
            norm_title = re.sub(r'\W+', ' ', item.title.lower()).strip()
            # Use top 5 words as a fingerprint if title is long enough
            words = norm_title.split()
            if len(words) > 3:
                fingerprint = " ".join(words[:5])
            else:
                fingerprint = norm_title
            
            if fingerprint not in counts:
                counts[fingerprint] = set()
            counts[fingerprint].add(item.source_name)
        
        # Convert set of sources to count
        return {k: len(v) for k, v in counts.items()}

    def _calculate_engagement_signal(self, item, max_engagement):
        if item.source_type == SourceType.REDDIT:
            metrics = item.engagement_metrics or {}
            ups = metrics.get('score', 0)
            comments = metrics.get('num_comments', 0)
            
            # Simple combined signal
            signal = ups + (comments * 2)
            if max_engagement > 0:
                return min(signal / max_engagement, 1.0)
        
        # News items don't have engagement metrics in this version
        return 0.0

    def _get_max_engagement(self, items):
        max_val = 0
        for item in items:
            if item.source_type == SourceType.REDDIT:
                metrics = item.engagement_metrics or {}
                val = metrics.get('score', 0) + (metrics.get('num_comments', 0) * 2)
                if val > max_val:
                    max_val = val
        return max_val

    def _calculate_coverage_signal(self, item, coverage_counts):
        norm_title = re.sub(r'\W+', ' ', item.title.lower()).strip()
        words = norm_title.split()
        fingerprint = " ".join(words[:5]) if len(words) > 3 else norm_title
        
        sources_count = coverage_counts.get(fingerprint, 1)
        
        # Boost based on number of sources: 1 source = 0, 2 = 0.5, 3+ = 1.0
        if sources_count <= 1:
            return 0.0
        if sources_count == 2:
            return 0.5
        return 1.0
