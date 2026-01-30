from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import ContentItem, SourceType
from datetime import datetime

def seed():
    init_db()
    db = SessionLocal()
    
    items = [
        ContentItem(
            title="Massive protests in Ottawa over new immigration policy",
            summary="Thousands gathered to protest the recent changes to the student visa program and border controls.",
            url="http://example.com/1",
            source_name="CBC News",
            source_type=SourceType.NEWS,
            country="Canada",
            controversy_score=85.0,
            engagement_metrics={"score": 500, "num_comments": 200},
            timestamp=datetime.now()
        ),
        ContentItem(
            title="India-Canada relations hit a new low over interference allegations",
            summary="New evidence suggests foreign influence in local elections, causing a diplomatic rift.",
            url="http://example.com/2",
            source_name="Times of India",
            source_type=SourceType.NEWS,
            country="India",
            controversy_score=90.0,
            engagement_metrics={"score": 800, "num_comments": 450},
            timestamp=datetime.now()
        ),
        ContentItem(
            title="Housing crisis worsens as inflation hits record high",
            summary="Economic analysts warn of a prolonged recession if interest rates are not adjusted.",
            url="http://example.com/3",
            source_name="r/CanadaPolitics",
            source_type=SourceType.REDDIT,
            country="Canada",
            controversy_score=75.0,
            engagement_metrics={"score": 1200, "num_comments": 600},
            timestamp=datetime.now()
        )
    ]
    
    db.add_all(items)
    db.commit()
    db.close()
    print("Seeded 3 items.")

if __name__ == "__main__":
    seed()
