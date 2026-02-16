# HansSays Automated Content Generator

A persistent, automated engine for ingesting, normalizing, and analyzing political news and social content from Canada and India.

## Core Architecture
This application is designed as a **persistent online service**, not a one-off script. It maintains an ongoing state and provides reusable outputs for downstream modules.

- **Persistent State**: All ingested data is stored in a structured SQLite database (`app.db`).
- **Autonomous Refresh**: A background scheduler performs a full ingestion cycle every 6 hours.
- **Unified Schema**: Data from multiple source types (News, Reddit) is normalized into a single schema for analysis.
- **REST API**: A FastAPI interface provides access to the unified feed, keyword filtering, and trending metrics.

## Trusted Sources

### News (RSS)
- **Canada**: CBC News, Global News, National Post, The Globe and Mail, The Hill Times.
- **India**: The Hindu, Indian Express, NDTV, Times of India, Economic Times.

### Social (Reddit)
- **Subreddits**: r/CanadaPolitics, r/IndiaSpeaks, r/IndiaNews.
- **Filters**: High upvotes (>50) and political keyword relevance matching.

## Application Endpoints
- `GET /items`: Fetch the unified feed (sorted chronologically). Supports `q`, `country`, `source_type`, and `limit` parameters.
- `GET /trending`: Get keyword-based categorical counts for current political topics.
- `POST /trigger-refresh`: Manually trigger a background ingestion cycle.

## How to Run
1. **Setup Environment**:
   ```bash
   pip3 install -r requirements.txt
   ```
2. **Launch Application**:
   ```bash
   # On Windows:
   py -m app.main

   # On macOS/Linux:
   python3 -m app.main
   ```
   The app runs on `http://localhost:8000`.

## Assumptions & Workflows
All project workflows assume this stateful, persistent architecture. Subsequent steps for ranking, clustering, or content generation will leverage the `ContentItem` model and the existing `app.db`.
