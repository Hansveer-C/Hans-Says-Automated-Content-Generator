from sqlalchemy.orm import Session
from textblob import TextBlob
from app.models import ContentItem, SourceType
from sqlalchemy import func
from datetime import datetime, timedelta
import re
from config import CONTROVERSIAL_TOPICS, STRONG_LANGUAGE

class ContentRanker:
    def __init__(self, db: Session):
        self.db = db

    def calculate_final_scores(self, lookback_hours=24):
        """
        Calculates and updates final_score for items ingested within lookback_hours
        using the new 40/20/20/20 engagement weighting and 0-100 controversy scale.
        """
        since = datetime.now() - timedelta(hours=lookback_hours)
        items = self.db.query(ContentItem).filter(ContentItem.timestamp >= since).all()
        
        if not items:
            return

        # 1. Calculate Coverage Signals (Cross-source repetition)
        coverage_counts = self._calculate_coverage_signals(items)

        # 2. Get Max Engagement for Normalization
        max_metrics = self._get_max_metrics(items)

        for item in items:
            # Step 2: Calculate Controversy Score (0-100)
            c_score, reason = self._calculate_controversy_details(item)
            item.controversy_score = c_score
            item.controversy_reason = reason

            # Step 3: Calculate Engagement Score (0-100)
            engagement_score = self._calculate_weighted_engagement(item, max_metrics, coverage_counts)
            
            # final_score = controversy_score + engagement_score
            item.final_score = round(item.controversy_score + engagement_score, 2)
        
        self.db.commit()

    def _calculate_controversy_details(self, item):
        """
        Calculates controversy_score (0-100) and controversy_reason.
        Based on sentiment intensity, charged language, topic sensitivity, and conflict framing.
        """
        score = 0.0
        reasons = []

        # 1. Topic Sensitivity
        sensitive_match = [t for t in CONTROVERSIAL_TOPICS if t.lower() in item.title.lower()]
        if sensitive_match:
            score += 40
            reasons.append(f"Topic matches sensitive areas: {', '.join(sensitive_match)}")

        # 2. Charged Language
        charged_words = [w for w in STRONG_LANGUAGE if re.search(rf'\b{w}\b', item.title.lower() + " " + (item.summary or "").lower())]
        if charged_words:
            # capped at 30
            score += min(len(charged_words) * 10, 30)
            reasons.append(f"Contains charged language: {', '.join(charged_words[:3])}")

        # 3. Sentiment Intensity (Conflict Framing)
        analysis = TextBlob(item.title + " " + (item.summary or ""))
        intensity = abs(analysis.sentiment.polarity) * analysis.sentiment.subjectivity
        if intensity > 0.3:
            score += 30
            reasons.append("High sentiment intensity and subjectivity detected")

        # Cap at 100
        final_c_score = min(score, 100.0)
        
        reason_text = " ".join(reasons) if reasons else "No specific controversy signals detected."
        return final_c_score, reason_text

    def _calculate_weighted_engagement(self, item, max_metrics, coverage_counts):
        """
        Calculates engagement_score using 40/20/20/20 weighting:
        - Reddit upvotes (40%)
        - Reddit comments (20%)
        - Headline intensity (20%)
        - Cross-source repetition (20%)
        """
        # Normalize each component to 0-25 (so they sum to 100 if all maxed out at 40/20/20/20 ratio? 
        # Actually 40% of 100 is 40 points.
        
        score = 0.0
        
        # 1. Reddit upvotes (40%)
        if item.source_type == SourceType.REDDIT:
            metrics = item.engagement_metrics or {}
            ups = metrics.get('score', 0)
            if max_metrics['ups'] > 0:
                score += (min(ups / max_metrics['ups'], 1.0)) * 40
        
        # 2. Reddit comments (20%)
        if item.source_type == SourceType.REDDIT:
            metrics = item.engagement_metrics or {}
            comments = metrics.get('num_comments', 0)
            if max_metrics['comments'] > 0:
                score += (min(comments / max_metrics['comments'], 1.0)) * 20

        # 3. Headline intensity (20%)
        analysis = TextBlob(item.title)
        intensity = abs(analysis.sentiment.polarity) * analysis.sentiment.subjectivity
        # Map 0-1 intensity to 0-20 score
        score += intensity * 20

        # 4. Cross-source repetition (20%)
        norm_title = re.sub(r'\W+', ' ', item.title.lower()).strip()
        words = norm_title.split()
        fingerprint = " ".join(words[:5]) if len(words) > 3 else norm_title
        sources_count = coverage_counts.get(fingerprint, 1)
        # Boost: 1 source = 0, 2 = 10, 3+ = 20
        if sources_count == 2:
            score += 10
        elif sources_count >= 3:
            score += 20

        return score

    def _calculate_coverage_signals(self, items):
        counts = {}
        for item in items:
            norm_title = re.sub(r'\W+', ' ', item.title.lower()).strip()
            words = norm_title.split()
            fingerprint = " ".join(words[:5]) if len(words) > 3 else norm_title
            
            if fingerprint not in counts:
                counts[fingerprint] = set()
            counts[fingerprint].add(item.source_name)
        return {k: len(v) for k, v in counts.items()}

    def _get_max_metrics(self, items):
        max_metrics = {'ups': 0, 'comments': 0}
        for item in items:
            if item.source_type == SourceType.REDDIT:
                metrics = item.engagement_metrics or {}
                ups = metrics.get('score', 0)
                comments = metrics.get('num_comments', 0)
                if ups > max_metrics['ups']: max_metrics['ups'] = ups
                if comments > max_metrics['comments']: max_metrics['comments'] = comments
        return max_metrics
