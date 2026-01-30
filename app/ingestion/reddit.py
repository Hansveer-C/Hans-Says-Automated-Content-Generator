import requests
import os
from sqlalchemy.orm import Session
from app.models import ContentItem, Source, SourceType
from app.analysis.controversy import ControversyAnalyzer
from datetime import datetime
import json
from dotenv import load_dotenv
from config import GET_ALL_KEYWORDS

load_dotenv()

def should_ingest_reddit(post_data, keywords, min_score=50):
    # Check "High Upvotes"
    if post_data.get('ups', 0) < min_score:
        return False
        
    # Check Keywords
    text_to_check = (post_data.get('title', '') + " " + (post_data.get('selftext', '') or "")).lower()
    if any(keyword.lower() in text_to_check for keyword in keywords):
        return True
        
    return False

def fetch_reddit_content(db: Session):
    # Use a custom User-Agent to satisfy Reddit's non-API request policy
    headers = {
        'User-Agent': 'HansSays:v1.0.0 (News Aggregator Bot)'
    }

    sources = db.query(Source).filter(Source.type == SourceType.REDDIT, Source.is_active == 1).all()

    for source in sources:
        print(f"Fetching Reddit (Non-API): r/{source.url}")
        try:
            url = f"https://www.reddit.com/r/{source.url}/hot.json?limit=50"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                item = post.get('data', {})
                if not should_ingest_reddit(item, GET_ALL_KEYWORDS):
                    continue
                    
                external_id = item.get('id')
                existing_item = db.query(ContentItem).filter(ContentItem.external_id == external_id).first()
                
                metrics = {
                    "score": item.get('ups', 0),
                    "num_comments": item.get('num_comments', 0),
                    "upvote_ratio": item.get('upvote_ratio', 0)
                }

                if existing_item:
                    existing_item.engagement_metrics = metrics
                    continue

                analyzer = ControversyAnalyzer()
                controversy_score = analyzer.analyze(item.get('title', ''), item.get('selftext') if item.get('is_self') else item.get('url'))

                new_item = ContentItem(
                    external_id=external_id,
                    source_type=SourceType.REDDIT,
                    source_name=source.name,
                    country=source.country,
                    title=item.get('title'),
                    summary=item.get('selftext') if item.get('is_self') else item.get('url'),
                    url=f"https://reddit.com{item.get('permalink')}",
                    timestamp=datetime.fromtimestamp(item.get('created_utc', 0)),
                    engagement_metrics=metrics,
                    controversy_score=controversy_score,
                    raw_json=json.dumps({"id": external_id})
                )
                db.add(new_item)
            db.commit()
            print(f"  - Successfully processed r/{source.url}")
        except Exception as e:
            print(f"  - Error processing r/{source.url}: {e}")
            db.rollback()
