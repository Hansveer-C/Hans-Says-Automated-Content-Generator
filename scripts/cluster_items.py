from app.database import SessionLocal
from app.models import ContentItem
from app.analysis.clustering import TopicClusterer

def cluster_top_items():
    db = SessionLocal()
    clusterer = TopicClusterer()
    
    # Fetch top controversial items that haven't been clustered yet (or re-cluster all top items)
    # For now, let's just cluster the top 100 most controversial items
    items = db.query(ContentItem).order_by(ContentItem.controversy_score.desc()).limit(100).all()
    
    print(f"Clustering {len(items)} items...")
    
    for item in items:
        old_cluster = item.cluster_id
        item.cluster_id = clusterer.categorize(item.title, item.summary)
        if old_cluster != item.cluster_id:
            print(f"Item: {item.title[:50]}... -> Cluster: {item.cluster_id}")
    
    db.commit()
    print("Clustering complete.")
    db.close()

if __name__ == "__main__":
    cluster_top_items()
