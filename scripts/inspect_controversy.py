from app.database import SessionLocal
from app.models import ContentItem

def show_controversial_items():
    db = SessionLocal()
    items = db.query(ContentItem).order_by(ContentItem.controversy_score.desc()).limit(10).all()
    
    print(f"{'Score':<6} | {'Cluster':<15} | {'Title'}")
    print("-" * 100)
    for item in items:
        print(f"{item.controversy_score:<6.3f} | {str(item.cluster_id):<15} | {item.title}")
        if item.summary:
            print(f"Summary: {item.summary[:150]}...")
        print("-" * 100)
    db.close()

if __name__ == "__main__":
    show_controversial_items()
