from app.database import SessionLocal
from app.models import ContentItem
from app.analysis.controversy import ControversyAnalyzer
import json

def update_scores():
    db = SessionLocal()
    analyzer = ControversyAnalyzer()
    
    items = db.query(ContentItem).all()
    print(f"Updating scores for {len(items)} items...")
    
    updated_count = 0
    for item in items:
        # Re-analyze based on title and summary
        new_score = analyzer.analyze(item.title, item.summary)
        
        if item.controversy_score != new_score:
            item.controversy_score = new_score
            updated_count += 1
            
    db.commit()
    db.close()
    print(f"Successfully updated {updated_count} items.")

if __name__ == "__main__":
    update_scores()
