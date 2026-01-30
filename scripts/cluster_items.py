from app.database import SessionLocal
from app.models import ContentItem
from app.analysis.clustering import TopicClusterer

def cluster_top_items():
    db = SessionLocal()
    clusterer = TopicClusterer()
    
    # Fetch items from the last 24 hours to ensure we can select the top ones
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(hours=24)
    items = db.query(ContentItem).filter(ContentItem.timestamp >= since).all()
    
    # Also fetch top 100 overall just in case
    top_items = db.query(ContentItem).order_by(ContentItem.controversy_score.desc()).limit(100).all()
    
    # Combine (unique)
    all_to_process = {item.id: item for item in items + top_items}.values()
    
    print(f"Clustering {len(all_to_process)} items...")
    
    for item in list(all_to_process):
        old_cluster = item.cluster_id
        item.cluster_id = clusterer.categorize(item.title, item.summary)
        if old_cluster != item.cluster_id:
            print(f"Item: {item.title[:50]}... -> Cluster: {item.cluster_id}")
    
    db.commit()
    print("Clustering complete.")
    db.close()

if __name__ == "__main__":
    cluster_top_items()
