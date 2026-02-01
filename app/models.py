from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class SourceType(enum.Enum):
    NEWS = "news"
    REDDIT = "reddit"

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(Enum(SourceType))
    url = Column(String)  # URL for RSS or Subreddit name for Reddit
    country = Column(String)
    is_active = Column(Integer, default=1)

class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # Link for RSS, ID for Reddit
    
    # Base Fields from User Request
    source_type = Column(Enum(SourceType))
    source_name = Column(String)
    country = Column(String)
    title = Column(String)
    summary = Column(Text)
    url = Column(String)
    timestamp = Column(DateTime)
    
    # Analysis & Scoring Fields
    engagement_metrics = Column(JSON, default={})  # Store hits, comments, upvotes, etc.
    controversy_score = Column(Float, default=0.0)
    controversy_reason = Column(Text, nullable=True) # Reason for the controversy score
    final_score = Column(Float, default=0.0)
    cluster_id = Column(String, index=True, nullable=True)
    used_for_content = Column(Boolean, default=False)
    
    # Metadata
    is_unavailable = Column(Boolean, default=False)
    enrichment_status = Column(String, default="original") # 'original', 'generated', 'failed'
    ingested_at = Column(DateTime, server_default=func.now())
    raw_json = Column(Text)  # Original payload

class TopicCommentary(Base):
    __tablename__ = "topic_commentaries"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, index=True)
    angles = Column(JSON)  # Store list of 3 angles (Critical, Comparative, Accountability)
    strongest_angle_html = Column(Text)  # The Facebook-ready version (formatted with line breaks etc)
    generated_at = Column(DateTime, server_default=func.now())

class TopicPackage(Base):
    """
    Stores the full 'Final Output Package' for a selected topic cluster.
    """
    __tablename__ = "topic_packages"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, index=True)
    date = Column(DateTime, server_default=func.now(), index=True)
    
    # Package Elements
    safe_article = Column(Text)
    safe_headlines = Column(JSON) # List of 3 headlines
    safe_cta = Column(String)
    pinned_comment = Column(Text)
    
    # Platform Expansion
    x_thread = Column(JSON) # List of post strings
    shorts_script = Column(Text)
    reels_script = Column(Text)
    seeding_pack = Column(JSON) # { platform: [comments] }
    
    carousel_slides = Column(JSON) # List of slide objects
    visual_directions = Column(JSON) # List of direction objects
    recommended_post_time = Column(DateTime)
    scheduling_metadata = Column(JSON) # timezone, why_this_time_works
