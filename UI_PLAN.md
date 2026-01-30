# HansSays UI/UX Implementation Plan

## 1. Design Philosophy
- **Dark Mode First**: Deep charcoal backgrounds with vibrant accent colors (e.g., Electric Blue or Neon Purple).
- **Premium Aesthetics**: Glassmorphism, subtle gradients, and micro-animations for interactions.
- **Card-Based Layout**: Each news/social item treated as a distinct visual unit with clear metadata.
- **Mobile Responsive**: Fluid grid system that adapts from desktop sidebars to mobile bottom navs.

## 2. Information Architecture (Routes)
- **`/` (Feed Dashboard)**: The "Live" center. Real-time stream of unified content with fast-filter chips (Immigration, Elections, etc.).
- **`/studio` (Content Studio)**: The "Analysis" hub. Tools for clustering items, generating summaries, and drafting social posts.
- **`/admin` (Admin Panel)**: The "Engine" room. Source management, ingestion logs, and system health stats.

## 3. Component Breakdown

### Core Layout
- `AppShell`: Persistent sidebar (desktop) / Drawer (mobile) with glassmorphism effect.
- `FeedGrid`: Masonry or auto-grid layout for content cards.

### Shared Components
- `NewsCard`: 
  - Headline + Source Badge (News vs Reddit).
  - Engagement Metrics (Upvotes/Comments for Reddit).
  - Quick Action Buttons (Analyze, Share, Bookmark).
- `FilterPill`: Horizontal scrollable list of trending keywords and country filters.
- `SearchHero`: Prominent search bar with "Trending Now" suggestions.

### Specialized Components
- `TrendChart`: Visual representation of topic frequency (for Studio/Admin).
- `SourceManager`: CRUD interface for RSS feeds and subreddits.
- `IngestionLog`: Live-updating terminal-style view for backend activities.

## 4. Tech Stack Preview
- **Frontend**: Vite + React + Tailwind CSS (for rapid premium styling).
- **Icons**: Lucide React for modern, thin-stroke icons.
- **Animations**: Framer Motion for smooth layout transitions.

## 5. Mockup Generation
I will generate a premium mockup of the **Feed Dashboard** to establish the visual direction.
