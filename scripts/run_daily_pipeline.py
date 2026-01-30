import sys
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.ingestion.rss import fetch_rss_feeds
from app.ingestion.reddit import fetch_reddit_content
from app.analysis.ranker import ContentRanker
from app.analysis.clustering import TopicClusterer
from app.analysis.commentary import ContentEngine
from app.analysis.enrichment import EnrichmentService
from app.models import ContentItem

def run_daily_pipeline():
    print("=== HANS SAYS DAILY PIPELINE STARTED ===")
    init_db()
    db = SessionLocal()
    
    try:
        # STEP 1: Ingest
        print("[1/4] Ingesting sources...")
        fetch_rss_feeds(db)
        fetch_reddit_content(db)
        
        # STEP 2 & 3: Score and Rank
        print("[2/4] Scoring and ranking controversy/engagement...")
        ranker = ContentRanker(db)
        ranker.calculate_final_scores()

        print("[2.5/4] Enriching items (Paywall & Summary pass)...")
        enricher = EnrichmentService()
        enricher.enrich_batch(db)
        
        # STEP 4: Cluster and Select
        print("[3/4] Clustering and selecting top topics...")
        clusterer = TopicClusterer()
        # Fetch top items for clustering
        items = db.query(ContentItem).order_by(ContentItem.final_score.desc()).limit(100).all()
        clusterer.cluster_items(items)
        db.commit()
        
        top_clusters = clusterer.select_top_clusters(items, n=2)
        print(f"Selected topics: {', '.join(top_clusters)}")
        
        # STEP 5-16: Generate Full Packages
        print("[4/4] Generating output packages...")
        engine = ContentEngine()
        for cluster_id in top_clusters:
            print(f"  - Generating package for: {cluster_id}")
            package = engine.generate_full_package(db, cluster_id)
            if package:
                print(f"    SUCCESS: Package created for {cluster_id}")
            else:
                print(f"    FAILED: Could not create package for {cluster_id}")
                
        print("=== PIPELINE COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"!!! PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    run_daily_pipeline()
