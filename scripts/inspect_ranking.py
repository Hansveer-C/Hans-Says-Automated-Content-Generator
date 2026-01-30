from app.database import SessionLocal
from app.models import ContentItem

def show_top_ranked():
    db = SessionLocal()
    items = db.query(ContentItem).order_by(ContentItem.final_score.desc()).limit(15).all()
    
    print(f"{'Final':<6} | {'Contr':<6} | {'Type':<6} | {'Title'}")
    print("-" * 100)
    for item in items:
        print(f"{item.final_score:<6.3f} | {item.controversy_score:<6.3f} | {item.source_type.value:<6} | {item.title}")
    db.close()

if __name__ == "__main__":
    show_top_ranked()
