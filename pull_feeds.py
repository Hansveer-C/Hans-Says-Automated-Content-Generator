import feedparser
import json
import requests
from config import RSS_FEEDS
from datetime import datetime

def fetch_feeds(feeds_dict):
    results = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for country, sources in feeds_dict.items():
        print(f"Fetching feeds for {country}...")
        results[country] = {}
        for source_name, url in sources.items():
            print(f"  - Pulling from: {source_name}")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                
                if not feed.entries:
                    # Try parsing without requests if it failed
                    feed = feedparser.parse(url)
                
                articles = []
                for entry in feed.entries[:5]:
                    articles.append({
                        "title": entry.get("title", "No Title"),
                        "link": entry.get("link", "No Link"),
                        "published": entry.get("published", entry.get("updated", "No Date")),
                        "summary": entry.get("summary", "No Summary")
                    })
                
                if not articles:
                    print(f"    Warning: No articles found for {source_name}")
                else:
                    print(f"    Found {len(articles)} articles.")
                    
                results[country][source_name] = articles
            except Exception as e:
                print(f"    Error fetching {source_name}: {e}")
                results[country][source_name] = []
    return results

def save_results(results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feed_pull_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    feed_data = fetch_feeds(RSS_FEEDS)
    save_results(feed_data)
