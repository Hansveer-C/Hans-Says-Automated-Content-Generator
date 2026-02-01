import feedparser
import requests
from sqlalchemy.orm import Session
from app.models import ContentItem, Source, SourceType
from app.analysis.controversy import ControversyAnalyzer
from app.analysis.filters import FilterService
from datetime import datetime, timedelta
import time
import json

def fetch_rss_feeds(db: Session):
    sources = db.query(Source).filter(Source.type == SourceType.NEWS, Source.is_active == 1).all()
    filter_service = FilterService()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (HansSays News Bot; v1.0.0)'
    }
    
    # Get recent items for similarity check
    recent_items = db.query(ContentItem).filter(ContentItem.timestamp >= datetime.now() - timedelta(hours=24)).all()
    
    for source in sources:
        print(f"Fetching RSS: {source.name}")
        try:
            response = requests.get(source.url, headers=headers, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                title = entry.get('title', 'No Title')
                summary = entry.get('summary', entry.get('description', ''))
                
                # 1. Eligibility Check
                if not filter_service.is_eligible(title, summary, source.name):
                    continue

                # 2. Hard Deduplication (URL)
                existing_item = db.query(ContentItem).filter(ContentItem.external_id == entry.link).first()
                if existing_item:
                    continue
                
                # 3. Advanced Deduplication (Similarity)
                is_duplicate = False
                for recent in recent_items:
                    if filter_service.jaccard_similarity(title, recent.title) > 0.7:
                        is_duplicate = True
                        break
                if is_duplicate:
                    continue
                
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                else:
                    pub_date = datetime.now()

                analyzer = ControversyAnalyzer()
                controversy_score = analyzer.analyze(entry.get('title', ''), entry.get('summary', entry.get('description', '')))

                new_item = ContentItem(
                    external_id=entry.link,
                    source_type=SourceType.NEWS,
                    source_name=source.name,
                    country=source.country,
                    title=entry.get('title', 'No Title'),
                    summary=entry.get('summary', entry.get('description', '')),
                    url=entry.link,
                    timestamp=pub_date,
                    engagement_metrics={}, # News rarely has engagement in RSS
                    controversy_score=controversy_score,
                    raw_json=json.dumps(entry)
                )
                db.add(new_item)
            db.commit()
            print(f"  - Successfully processed {source.name}")
        except Exception as e:
            print(f"  - Error processing {source.name}: {e}")
            db.rollback()
