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
    final_score = Column(Float, default=0.0)
    cluster_id = Column(String, index=True, nullable=True)
    used_for_content = Column(Boolean, default=False)
    
    # Metadata
    ingested_at = Column(DateTime, server_default=func.now())
    raw_json = Column(Text)  # Original payload
