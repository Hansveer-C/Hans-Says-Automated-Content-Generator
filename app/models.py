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
    
    # 1. Canonical Source Outputs
    primary_topic = Column(String)
    secondary_topic = Column(String)
    core_thesis = Column(Text)
    editorial_angle = Column(String)
    
    # 2. Facebook Page Package
    facebook_article = Column(Text) # 300-400 words
    facebook_headlines = Column(JSON) # 3 options
    facebook_cta = Column(String)
    facebook_pinned_comment = Column(Text)
    
    # 3. Facebook Groups Package
    facebook_group_post = Column(Text) # conversational/question-forward
    facebook_group_pinned_comment = Column(Text)
    group_posting_guidance = Column(Text)
    
    # 4. Instagram Reels Package
    ig_reel_script = Column(JSON) # on-screen text beats
    ig_caption = Column(Text)
    ig_hashtags = Column(JSON) # 3-7 tags
    ig_seed_comments = Column(JSON) # 3
    ig_pin_comment = Column(Text)
    
    # 5. YouTube Shorts Package
    yt_shorts_script = Column(Text) # timestamped
    yt_title = Column(String)
    yt_description = Column(Text)
    yt_pinned_comment = Column(Text)
    yt_seed_comments = Column(JSON) # 3
    
    # 6. X (Twitter) Package
    x_primary_post = Column(String) # <= 280 chars
    x_thread_replies = Column(JSON) # 2-4 optional
    x_hashtags = Column(JSON) # 0-2 max
    
    # 7. Carousel / Slide Video Package
    carousel_slides = Column(JSON) # 6-8 slides, visual info
    carousel_caption = Column(Text)
    
    # 8. Comment Seeding & Engagement Pack
    pinned_comment_strategy = Column(Text)
    seed_comments_per_platform = Column(JSON)
    creator_reply_templates = Column(JSON) # Agree, Neutral, Calm disagreement
    
    # 9. Scheduling & Deployment Plan
    recommended_post_times = Column(JSON) # Per platform
    platform_posting_order = Column(JSON) # Platform list
    staggered_timing_offsets = Column(JSON)
    posting_reason = Column(Text)
    next_action = Column(String, default="wait") # post now / wait / scheduled
    today_queue_position = Column(Integer)
    
    # 10. Operator Control Outputs
    status_flags = Column(JSON, default={"generated": True, "copied": False, "scheduled": False, "posted": False})
    posted_at = Column(DateTime, nullable=True)
    notes = Column(Text)
