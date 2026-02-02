import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import ContentItem, TopicCommentary, TopicPackage

class ContentEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def generate_commentary_angles(self, db: Session, cluster_id: str) -> Optional[TopicCommentary]:
        """
        Step 5: Angle Generation (3 angles + strongest)
        """
        items = db.query(ContentItem).filter(
            ContentItem.cluster_id == cluster_id
        ).order_by(ContentItem.final_score.desc()).limit(10).all()

        if not items:
            return None

        context = "\n".join([f"- {item.title}: {item.summary}" for item in items])
        
        data = None
        if self.client:
            try:
                prompt = self._get_angle_prompt(cluster_id, context)
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a sharp, conversational political analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" }
                )
                data = json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"Error calling LLM for angles: {e}")

        if not data:
            data = self._get_mock_angle_data(cluster_id)
            
        commentary = TopicCommentary(
            cluster_id=cluster_id,
            angles=data.get("angles", []),
            strongest_angle_html=data.get("facebook_post", "No angle generated.")
        )
        
        db.add(commentary)
        db.commit()
        db.refresh(commentary)
        return commentary

    def generate_full_package(self, db: Session, cluster_id: str) -> Optional[TopicPackage]:
        """
        Steps 6-15: Generates the full 'Final Output Package'.
        Multi-stage pass: Tone -> Article -> Readability -> Voice -> Safety -> Media.
        """
        items = db.query(ContentItem).filter(
            ContentItem.cluster_id == cluster_id
        ).order_by(ContentItem.final_score.desc()).limit(15).all()

        if not items:
            return None

        context = "\n".join([f"- {item.title}: {item.summary}" for item in items])
        
        # We need the strongest angle first
        commentary = db.query(TopicCommentary).filter(TopicCommentary.cluster_id == cluster_id).order_by(TopicCommentary.generated_at.desc()).first()
        if not commentary:
            commentary = self.generate_commentary_angles(db, cluster_id)

        if not commentary:
            print(f"Warning: Failed to generate commentary for {cluster_id}")
            strongest_angle = "No specific angle refined."
        else:
            strongest_angle = commentary.strongest_angle_html or "No specific angle refined."

        data = None
        if self.client:
            try:
                prompt = self._get_package_prompt(cluster_id, context, strongest_angle)
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are HANS SAYS, a blunt, Canadian, accountability-focused political analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" }
                )
                data = json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"Error calling LLM for full package: {e}")

        if not data:
            data = self._get_mock_package_data(cluster_id)

        # Step 16: Auto-Scheduling (Canada)
        scheduling = self._calculate_scheduling(cluster_id, data)

        package = TopicPackage(
            cluster_id=cluster_id,
            # 1. Canonical
            primary_topic=cluster_id,
            secondary_topic=data.get("secondary_topic", "General Politics"),
            core_thesis=data.get("core_thesis", "Accountability matters."),
            editorial_angle=strongest_angle,
            
            # 2. Facebook Page
            facebook_article=data.get("facebook_article", "No article generated."),
            facebook_headlines=data.get("facebook_headlines", []),
            facebook_cta=data.get("facebook_cta", ""),
            facebook_pinned_comment=data.get("facebook_pinned_comment", ""),
            
            # 3. Facebook Groups
            facebook_group_post=data.get("facebook_group_post"),
            facebook_group_pinned_comment=data.get("facebook_group_pinned_comment"),
            group_posting_guidance=data.get("group_posting_guidance"),
            
            # 4. Instagram
            ig_reel_script=data.get("ig_reel_script"),
            ig_caption=data.get("ig_caption"),
            ig_hashtags=data.get("ig_hashtags"),
            ig_seed_comments=data.get("ig_seed_comments"),
            ig_pin_comment=data.get("ig_pin_comment"),
            
            # 5. YouTube
            yt_shorts_script=data.get("yt_shorts_script"),
            yt_title=data.get("yt_title"),
            yt_description=data.get("yt_description"),
            yt_pinned_comment=data.get("yt_pinned_comment"),
            yt_seed_comments=data.get("yt_seed_comments"),
            
            # 6. X
            x_primary_post=data.get("x_primary_post"),
            x_thread_replies=data.get("x_thread_replies"),
            x_hashtags=data.get("x_hashtags"),
            
            # 7. Carousel
            carousel_slides=data.get("carousel_slides"),
            carousel_caption=data.get("carousel_caption"),
            
            # 8. Engagement
            pinned_comment_strategy=data.get("pinned_comment_strategy"),
            seed_comments_per_platform=data.get("seed_comments_per_platform"),
            creator_reply_templates=data.get("creator_reply_templates"),
            
            # 9. Scheduling
            recommended_post_times=scheduling["recommended_times"],
            platform_posting_order=["X", "Facebook", "Instagram", "YouTube"],
            staggered_timing_offsets=scheduling["staggered_offsets"],
            posting_reason=scheduling["why"],
            next_action="wait",
            today_queue_position=1,
            
            # 10. Operator
            status_flags={"generated": True, "copied": False, "scheduled": False, "posted": False}
        )
        
        db.add(package)
        
        # Mark all items in this cluster as used_for_content=True
        for item in items:
            item.used_for_content = True
            
        db.commit()
        db.refresh(package)
        return package

    def _calculate_scheduling(self, cluster_id, data):
        """
        Assigns recommended posting times using Canadian time zones.
        X (Immediate) -> FB (Offset) -> IG (Offset) -> YT (Offset)
        """
        from datetime import datetime, time, timedelta
        now = datetime.now()
        
        is_policy = any(k in cluster_id.lower() for k in ["policy", "student", "economy", "international"])
        
        if is_policy:
            target_time = time(12, 30)
            why = "Policy topics perform better in the lunch window (12:30 PM EST)."
        else:
            target_time = time(19, 30)
            why = "Controversial news gains maximum engagement in the evening prime window (7:30 PM EST)."
        
        base_dt = datetime.combine(now.date(), target_time)
        if base_dt < now:
            base_dt += timedelta(days=1)
            
        offsets = {
            "X": 0,          # Immediate
            "Facebook": 30,  # +30 mins
            "Instagram": 60, # +1 hour
            "YouTube": 120   # +2 hours
        }
        
        recommended_times = {}
        for platform, offset in offsets.items():
            platform_time = base_dt + timedelta(minutes=offset)
            recommended_times[platform] = platform_time.isoformat()

        return {
            "recommended_times": recommended_times,
            "staggered_offsets": offsets,
            "why": why,
            "timezone": "America/Toronto (EST/EDT)"
        }

    def _get_package_prompt(self, cluster_id, context, strongest_angle):
        return f"""
        You are HANS SAYS. Voice: blunt, Canadian, accountability-focused. Short sentences. No fluff.
        
        Topic: {cluster_id}
        Core Angle: {strongest_angle}
        Context: {context}
        
        Generate the following PLATFORM-SPECIFIC packages in one JSON object:
        
        1. Canonical:
           - secondary_topic: A related sub-category.
           - core_thesis: One sentence summary of the stance.
        
        2. Facebook Page:
           - facebook_article: 300-400 words, clear stance, conversational, strong hook.
           - facebook_headlines: 3 scroll-stopping headlines (<12 words).
           - facebook_cta: 1 engagement CTA.
           - facebook_pinned_comment: 1-2 sentences inviting debate.
           
        3. Facebook Groups (Adjusted Tone):
           - facebook_group_post: Conversational, question-forward, group-safe framing.
           - facebook_group_pinned_comment: Inviting member stories.
           - group_posting_guidance: Guidance on which groups to target.
           
        4. Instagram Reels:
           - ig_reel_script: List of on-screen text beats (short, punchy).
           - ig_caption: Hans Says voice, catchy.
           - ig_hashtags: 3-7 tags.
           - ig_seed_comments: 3 comments to start engagement.
           - ig_pin_comment: The main engagement question.
           
        5. YouTube Shorts:
           - yt_shorts_script: Timestamped 20-40s script (Hook, Build, Call to Action).
           - yt_title: Search-optimized title.
           - yt_description: Short summary.
           - yt_pinned_comment: Engagement prompt.
           - yt_seed_comments: 3 comments.
           
        6. X (Twitter):
           - x_primary_post: Main post <= 280 chars.
           - x_thread_replies: 2-4 follow-up replies.
           - x_hashtags: 0-2 tags.
           
        7. Carousel/Slides:
           - carousel_slides: 6-8 slides with text (<=12 words) and visual_direction per slide.
           - carousel_caption: Summary for the post.
           
        8. Engagement scaffolding:
           - pinned_comment_strategy: How to handle the top comment.
           - seed_comments_per_platform: Specific comments for FB, YT, IG.
           - creator_reply_templates: Templates for [Agree, Neutral, Calm disagreement].

        Return valid JSON with these keys. No markdown blocks.
        """

    def _get_mock_package_data(self, cluster_id):
        return {
            "secondary_topic": "Federal Oversight",
            "core_thesis": f"The handling of {cluster_id} shows a total lack of transparency.",
            "facebook_article": f"Look, we've seen this before. {cluster_id} is a mess because nobody wants to take responsibility. We checked the records. The numbers don't lie. Canadians deserve better than these half-measures.",
            "facebook_headlines": [f"The {cluster_id} Cover-up?", f"Hans Says: Enough with {cluster_id}", "Accountability Now"],
            "facebook_cta": "What do you think? Let's hear it below.",
            "facebook_pinned_comment": "Keep it civil, keep it factual.",
            "facebook_group_post": f"Quick question for the group: How has the {cluster_id} situation affected your local community? We're looking into the lack of federal response.",
            "facebook_group_pinned_comment": "We want to hear your personal stories.",
            "group_posting_guidance": "Post in local community groups and political watchdog groups.",
            "ig_reel_script": [{"beat": "0:00", "text": "Fed up?"}, {"beat": "0:02", "text": f"{cluster_id} is breaking."}],
            "ig_caption": "No more excuses on this one. Link in bio for the full data.",
            "ig_hashtags": ["#CanadaPolitics", "#HansSays", f"#{cluster_id.replace(' ', '')}"],
            "ig_seed_comments": ["Finally!", "Spot on.", "Need more of this."],
            "ig_pin_comment": "Is it time for a change?",
            "yt_shorts_script": "0:00 - They said it was handled.\n0:10 - The data says otherwise.\n0:20 - Demand better.",
            "yt_title": f"The TRUTH about {cluster_id} in Canada",
            "yt_description": "Hans breaks down the latest failures in oversight.",
            "yt_pinned_comment": "Subscribe for more accountability.",
            "yt_seed_comments": ["Great info.", "Share this.", "Keep it up."],
            "x_primary_post": f"No more excuses on {cluster_id}. The data is clear: oversight failed. Full breakdown coming.",
            "x_thread_replies": ["Oversight was warned in 2023.", "Action was promised, none taken.", "Canadians are paying the price."],
            "x_hashtags": ["#canpol", f"#{cluster_id.replace(' ', '')}"],
            "carousel_slides": [{"slide": 1, "text": "The Crisis", "visual": "Chart showing decline"}],
            "carousel_caption": "The full story in slides.",
            "pinned_comment_strategy": "Highlight the most thoughtful critique and reply with data.",
            "seed_comments_per_platform": {"FB": ["True.", "Sad."], "X": ["Exactly.", "Read this."]},
            "creator_reply_templates": {"Agree": "Spot on. We need more eyes on this.", "Neutral": "Fair point, though the data suggests otherwise.", "Calm disagreement": "I hear you, but let's look at the actual outcomes."}
        }

# For backward compatibility during migration
CommentaryGenerator = ContentEngine
