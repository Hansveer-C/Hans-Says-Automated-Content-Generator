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
    Each platform has an explicit set of fields representing its output contract.
    """
    __tablename__ = "topic_packages"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, index=True)
    date = Column(DateTime, server_default=func.now(), index=True)
    
    # 1. Canonical Source Outputs
    primary_topic = Column(String)
    secondary_topic = Column(String)
    core_thesis = Column(Text)
    editorial_angle = Column(Text)
    
    # 2. Facebook Page (facebook_page_post)
    facebook_post_body = Column(Text) # 300-400 words
    facebook_headlines = Column(JSON) # Array of 3
    facebook_cta = Column(String)
    facebook_pinned_comment = Column(Text)
    facebook_distribution_safe_version = Column(Text)
    facebook_metadata = Column(JSON) # recommended_post_time, timezone, post_intent, status
    
    # 3. Facebook Groups (facebook_group_post)
    facebook_group_post_body = Column(Text) # 150-250 words
    facebook_group_discussion_prompt = Column(Text)
    facebook_group_safety_notes = Column(Text)
    facebook_group_metadata = Column(JSON) # group_safe_score, recommended_delay, status
    
    # 4. Instagram Reels (instagram_reel)
    ig_reel_script = Column(JSON) # timestamped visual beats
    ig_on_screen_text = Column(JSON) # Array of slide/beat text
    ig_caption = Column(Text)
    ig_seed_comment = Column(Text)
    ig_hashtags = Column(JSON) # preserved from before
    ig_metadata = Column(JSON) # audio_guidance, recommended_post_time, status
    
    # 5. YouTube Shorts (youtube_short)
    yt_shorts_script = Column(Text) # timestamped beats
    yt_title = Column(String)
    yt_description = Column(Text)
    yt_pinned_comment = Column(Text)
    yt_metadata = Column(JSON) # retention_hook_used, recommended_post_time, status
    
    # 6. X Twitter (x_post)
    x_primary_post = Column(String) # <= 280 chars
    x_thread_replies = Column(JSON) # 2-4
    x_engagement_question = Column(String)
    x_metadata = Column(JSON) # post_type, recommended_post_time, status
    
    # 7. Comment Seeding (comment_seeding_pack)
    seeding_yt_comments = Column(JSON) # 3
    seeding_ig_comments = Column(JSON) # 3
    seeding_pin_recommendation = Column(Text)
    seeding_follow_up_timing = Column(String)
    seeding_creator_reply_templates = Column(JSON) # Agree, Neutral, Calm disagreement
    
    # 8. Carousel (carousel_asset)
    carousel_slides = Column(JSON) # 6-8 slides with text, visual_direction, text_style
    carousel_caption = Column(Text)
    carousel_metadata = Column(JSON)
    
    # 9. Operator & Queue Management (inherited)
    status_flags = Column(JSON, default={"generated": True, "copied": False, "scheduled": False, "posted": False})
    posted_at = Column(DateTime, nullable=True)
    notes = Column(Text)
    today_queue_position = Column(Integer)
    next_action = Column(String, default="wait")
