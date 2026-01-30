from app.database import SessionLocal
from app.analysis.ranker import ContentRanker

def run_ranking():
    db = SessionLocal()
    ranker = ContentRanker(db)
    print("Calculating scores for all items in the last 7 days...")
    # Increase lookback for one-time update
    ranker.calculate_final_scores(lookback_hours=168) 
    db.close()
    print("Done.")

if __name__ == "__main__":
    run_ranking()
