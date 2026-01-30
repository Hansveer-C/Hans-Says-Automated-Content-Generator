from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import init_db, get_db, SessionLocal
from app.models import Source, ContentItem, SourceType, TopicCommentary
from app.scheduler import start_scheduler
from app.analysis.commentary import CommentaryGenerator
import uvicorn
import os

app = FastAPI(title="HansSays Automated Content Generator")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    init_db()
    
    db = SessionLocal()
    if db.query(Source).count() == 0:
        seed_sources(db)
    db.close()
    
    start_scheduler()

def seed_sources(db: Session):
    from config import RSS_FEEDS
    
    # RSS Sources from Config
    for country, sources in RSS_FEEDS.items():
        for name, url in sources.items():
            if not db.query(Source).filter(Source.name == name).first():
                source = Source(name=name, url=url, type=SourceType.NEWS, country=country)
                db.add(source)
    
    # Updated Reddit Sources
    reddit_sources = [
        ("r/CanadaPolitics", "CanadaPolitics", "Canada"),
        ("r/IndiaSpeaks", "IndiaSpeaks", "India"),
        ("r/IndiaNews", "IndiaNews", "India"),
    ]
    
    for name, sub, country in reddit_sources:
        if not db.query(Source).filter(Source.name == name).first():
            source = Source(name=name, url=sub, type=SourceType.REDDIT, country=country)
            db.add(source)
            
    db.commit()

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/items")
def get_items(
    q: str = None, 
    country: str = None, 
    source_type: str = None, # 'news', 'reddit', or None for all
    sort_by: str = "timestamp", # 'timestamp', 'final_score', or 'controversy_score'
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(ContentItem)
    
    if country:
        query = query.filter(ContentItem.country == country)
    
    if source_type:
        if source_type.lower() == "news":
            query = query.filter(ContentItem.source_type == SourceType.NEWS)
        elif source_type.lower() == "reddit":
            query = query.filter(ContentItem.source_type == SourceType.REDDIT)
        
    if q:
        search = f"%{q}%"
        query = query.filter((ContentItem.title.ilike(search)) | (ContentItem.summary.ilike(search)))
    
    # Sorting
    if sort_by == "final_score":
        query = query.order_by(ContentItem.final_score.desc())
    elif sort_by == "controversy_score":
        query = query.order_by(ContentItem.controversy_score.desc())
    else:
        query = query.order_by(ContentItem.timestamp.desc())
        
    items = query.limit(limit).all()
    return items

@app.get("/trending")
def get_trending_topics(db: Session = Depends(get_db)):
    from config import POLITICAL_KEYWORDS
    results = {}
    for category, terms in POLITICAL_KEYWORDS.items():
        filters = []
        for term in terms:
            filters.append(ContentItem.title.ilike(f"%{term}%"))
            filters.append(ContentItem.summary.ilike(f"%{term}%"))
        
        from sqlalchemy import or_
        count = db.query(ContentItem).filter(or_(*filters)).count()
        results[category] = count
        
    return results

@app.post("/topics/{cluster_id}/generate_angles")
def generate_topic_angles(cluster_id: str, db: Session = Depends(get_db)):
    generator = CommentaryGenerator()
    commentary = generator.generate_for_cluster(db, cluster_id)
    if not commentary:
        return {"error": "No items found for this topic"}
    return commentary

@app.get("/topics/{cluster_id}/angles")
def get_topic_angles(cluster_id: str, db: Session = Depends(get_db)):
    commentary = db.query(TopicCommentary).filter(
        TopicCommentary.cluster_id == cluster_id
    ).order_by(TopicCommentary.generated_at.desc()).first()
    
    if not commentary:
        return {"error": "No commentary found for this topic"}
    return commentary

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
