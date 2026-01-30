import os
import requests
from typing import Optional
from sqlalchemy.orm import Session
from app.models import ContentItem, SourceType
from openai import OpenAI

class EnrichmentService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def process_item(self, db: Session, item: ContentItem):
        """
        Enriches a single item if it's missing a summary or likely paywalled.
        """
        if item.summary and len(item.summary) > 50 and not self._is_paywall_likely(item):
            return

        print(f"Enriching item: {item.title}")
        
        # 1. Attempt to fetch summary via LLM if we have the title/URL context
        summary = self._fetch_fallback_summary(item)
        
        if summary:
            item.summary = summary
            item.enrichment_status = "generated"
        else:
            item.is_unavailable = True
            item.enrichment_status = "failed"
        
        db.commit()

    def _is_paywall_likely(self, item: ContentItem) -> bool:
        """
        Heuristic check for common paywalled domains or indicators.
        """
        paywalled_domains = ["nytimes.com", "wsj.com", "theglobeandmail.com", "thestar.com"]
        return any(domain in item.url for domain in paywalled_domains)

    def _fetch_fallback_summary(self, item: ContentItem) -> Optional[str]:
        """
        Uses LLM to generate a summary based on the title and any snippet available.
        In a real scenario, this might call a specialized news API.
        """
        if not self.client:
            return None

        try:
            prompt = f"Summarize this news headline in 2-3 concise sentences for a political feed: {item.title}"
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a concise political news summarizer."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Enrichment error: {e}")
            return None

    def enrich_batch(self, db: Session, limit: int = 20):
        """
        Enriches a batch of items that need it.
        """
        items = db.query(ContentItem).filter(
            ContentItem.enrichment_status == "original"
        ).order_by(ContentItem.timestamp.desc()).limit(limit).all()
        
        for item in items:
            self.process_item(db, item)
