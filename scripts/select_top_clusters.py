from app.database import SessionLocal
from app.models import ContentItem
from datetime import datetime, timedelta
from sqlalchemy import func
import json

def select_top_clusters():
    db = SessionLocal()
    
    # 1. Filter items from the last 24 hours
    since = datetime.now() - timedelta(hours=24)
    
    # 2. Aggregate controversy scores by cluster
    # We ignore 'other' cluster as it's not a clear topic
    results = db.query(
        ContentItem.cluster_id,
        func.avg(ContentItem.controversy_score).label('avg_score'),
        func.count(ContentItem.id).label('item_count')
    ).filter(
        ContentItem.timestamp >= since,
        ContentItem.cluster_id != 'other',
        ContentItem.cluster_id.isnot(None)
    ).group_by(
        ContentItem.cluster_id
    ).order_by(
        func.avg(ContentItem.controversy_score).desc()
    ).limit(2).all()
    
    if not results:
        print("No controversial clusters found in the last 24 hours.")
        db.close()
        return

    print("Top Controversial Topic Clusters (Last 24 Hours):")
    print("=" * 60)
    
    for cluster_id, avg_score, item_count in results:
        print(f"TOPIC: {cluster_id.upper()} | AVG SCORE: {avg_score:.3f} | COUNT: {item_count}")
        
        top_items = db.query(ContentItem).filter(
            ContentItem.timestamp >= since,
            ContentItem.cluster_id == cluster_id
        ).order_by(ContentItem.controversy_score.desc()).limit(2).all()
        
        for item in top_items:
            print(f"  - {item.title[:80]}... ({item.controversy_score:.3f})")
        print("-" * 40)
        
    db.close()

if __name__ == "__main__":
    select_top_clusters()
