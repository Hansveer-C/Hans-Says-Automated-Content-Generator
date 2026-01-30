from textblob import TextBlob
from config import CONTROVERSIAL_TOPICS, STRONG_LANGUAGE
import re

class ControversyAnalyzer:
    def __init__(self):
        self.topics = [t.lower() for t in CONTROVERSIAL_TOPICS]
        self.strong_language = [s.lower() for s in STRONG_LANGUAGE]

    def analyze(self, title: str, summary: str) -> float:
        """
        Analyzes content for political controversy.
        Returns a score between 0.0 and 1.0.
        """
        text = f"{title} {summary or ''}".lower()
        score = 0.0
        
        # 1. Sentiment Polarity (0.3 weight)
        # Highly positive or highly negative sentiment can indicate controversy
        try:
            blob = TextBlob(text)
            polarity = abs(blob.sentiment.polarity)
            # Normalize: polarity is -1 to 1, so abs is 0 to 1.
            # We want to flag extreme sentiment.
            score += polarity * 0.3
        except:
            pass

        # 2. Strong Language (0.4 weight)
        # Presence of inflammatory words
        found_strong_words = 0
        for word in self.strong_language:
            if re.search(rf'\b{re.escape(word)}\b', text):
                found_strong_words += 1
        
        if found_strong_words > 0:
            # Scale score based on number of strong words, maxing out at 0.4
            score += min(found_strong_words * 0.1, 0.4)

        # 3. Topic Sensitivity (0.3 weight)
        # Presence of known controversial topics
        found_topics = 0
        for topic in self.topics:
            if topic in text:
                found_topics += 1
        
        if found_topics > 0:
            # Scale score based on number of topics, maxing out at 0.3
            score += min(found_topics * 0.1, 0.3)

        return min(round(score, 3), 1.0)
