from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.ingestion.rss import fetch_rss_feeds
from app.ingestion.reddit import fetch_reddit_content
from app.analysis.ranker import ContentRanker
import os

def run_ingestion_cycle():
    print("Starting ingestion cycle...")
    db = SessionLocal()
    try:
        fetch_rss_feeds(db)
        fetch_reddit_content(db)
        
        print("Ranking items...")
        ranker = ContentRanker(db)
        ranker.calculate_final_scores()
        
        print("Ingestion cycle completed.")
    except Exception as e:
        print(f"Error in ingestion cycle: {e}")
    finally:
        db.close()

def start_scheduler():
    refresh_hours = int(os.getenv("REFRESH_INTERVAL_HOURS", 6))
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_ingestion_cycle, 'interval', hours=refresh_hours)
    scheduler.start()
    print(f"Scheduler started. Refreshing every {refresh_hours} hours.")
    # Run once in background at startup
    scheduler.add_job(run_ingestion_cycle, 'date')
