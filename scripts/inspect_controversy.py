from app.database import SessionLocal
from app.models import ContentItem

def show_controversial_items():
    db = SessionLocal()
    items = db.query(ContentItem).order_by(ContentItem.controversy_score.desc()).limit(10).all()
    
    print(f"{'Score':<6} | {'Type':<6} | {'Country':<7} | {'Title'}")
    print("-" * 80)
    for item in items:
        print(f"{item.controversy_score:<6.3f} | {item.source_type.value:<6} | {item.country:<7} | {item.title}")
    db.close()

if __name__ == "__main__":
    show_controversial_items()
