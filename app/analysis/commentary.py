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
            secondary_topic=data.get("canonical", {}).get("secondary_topic", "General Politics"),
            core_thesis=data.get("canonical", {}).get("core_thesis", "Accountability matters."),
            editorial_angle=strongest_angle,
            
            # 2. Facebook Page
            facebook_post_body=data.get("facebook_page_post", {}).get("post_body"),
            facebook_headlines=data.get("facebook_page_post", {}).get("headlines"),
            facebook_cta=data.get("facebook_page_post", {}).get("cta"),
            facebook_pinned_comment=data.get("facebook_page_post", {}).get("pinned_comment"),
            facebook_distribution_safe_version=data.get("facebook_page_post", {}).get("distribution_safe_version"),
            facebook_metadata=data.get("facebook_page_post", {}).get("metadata"),
            
            # 3. Facebook Groups
            facebook_group_post_body=data.get("facebook_group_post", {}).get("post_body"),
            facebook_group_discussion_prompt=data.get("facebook_group_post", {}).get("discussion_prompt"),
            facebook_group_safety_notes=data.get("facebook_group_post", {}).get("safety_notes"),
            facebook_group_metadata=data.get("facebook_group_post", {}).get("metadata"),
            
            # 4. Instagram
            ig_reel_script=data.get("instagram_reel", {}).get("reel_script"),
            ig_on_screen_text=data.get("instagram_reel", {}).get("on_screen_text"),
            ig_caption=data.get("instagram_reel", {}).get("caption"),
            ig_seed_comment=data.get("instagram_reel", {}).get("seed_comment"),
            ig_hashtags=data.get("instagram_reel", {}).get("hashtags", []),
            ig_metadata=data.get("instagram_reel", {}).get("metadata"),
            
            # 5. YouTube
            yt_shorts_script=data.get("youtube_short", {}).get("shorts_script"),
            yt_title=data.get("youtube_short", {}).get("title"),
            yt_description=data.get("youtube_short", {}).get("description"),
            yt_pinned_comment=data.get("youtube_short", {}).get("pinned_comment"),
            yt_metadata=data.get("youtube_short", {}).get("metadata"),
            
            # 6. X
            x_primary_post=data.get("x_post", {}).get("primary_post"),
            x_thread_replies=data.get("x_post", {}).get("thread_replies"),
            x_engagement_question=data.get("x_post", {}).get("engagement_question"),
            x_metadata=data.get("x_post", {}).get("metadata"),
            
            # 7. Comment Seeding
            seeding_yt_comments=data.get("comment_seeding_pack", {}).get("yt_seed_comments"),
            seeding_ig_comments=data.get("comment_seeding_pack", {}).get("ig_seed_comments"),
            seeding_pin_recommendation=data.get("comment_seeding_pack", {}).get("pin_recommendation"),
            seeding_follow_up_timing=data.get("comment_seeding_pack", {}).get("follow_up_timing"),
            seeding_creator_reply_templates=data.get("comment_seeding_pack", {}).get("creator_reply_templates"),
            
            # 8. Carousel
            carousel_slides=data.get("carousel_asset", {}).get("slides"),
            carousel_caption=data.get("carousel_asset", {}).get("caption"),
            carousel_metadata=data.get("carousel_asset", {}).get("metadata"),
            
            # 9. Operator
            status_flags={"generated": True, "copied": False, "scheduled": False, "posted": False},
            today_queue_position=1,
            next_action="wait"
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
        
        1. canonical:
           - secondary_topic: A related sub-category.
           - core_thesis: One sentence summary of the stance.
        
        2. facebook_page_post:
           - post_body: 300-400 words, clear stance, conversational, strong hook. mobile-formatted (1-2 line paragraphs).
           - headlines: 3 scroll-stopping options (<=12 words each).
           - cta: 1-2 engagement-oriented sentences.
           - pinned_comment: 1-2 open-ended sentences inviting debate.
           - distribution_safe_version: Final, softened-claim version of the post_body.
           - metadata: {{ "recommended_post_time": "ISO string", "timezone": "America/Toronto", "post_intent": "accountability", "status": "generated" }}
           
        3. facebook_group_post:
           - post_body: 150-250 words, conversational, question-forward.
           - discussion_prompt: Explicit question for members.
           - safety_notes: Note on why phrasing is group-safe.
           - metadata: {{ "group_safe_score": 0.9, "recommended_delay": "+45 min", "status": "generated" }}
           
        4. instagram_reel:
           - reel_script: 20-35s script with visual beats.
           - on_screen_text: Array of 5-8 short text bursts (<=10 words each).
           - caption: 2 short paragraphs, ends with 3-5 hashtags.
           - seed_comment: 1 open-ended question.
           - metadata: {{ "audio_guidance": "voiceover", "recommended_post_time": "ISO string", "status": "generated" }}
           
        5. youtube_short:
           - shorts_script: 20-40s timestamped script (Hook, Build, CTA).
           - title: <=70 characters, curiosity-driven.
           - description: 1-2 sentence summary.
           - pinned_comment: Accountability or clarification question.
           - metadata: {{ "retention_hook_used": true, "recommended_post_time": "ISO string", "status": "generated" }}
           
        6. x_post:
           - primary_post: Main post <= 280 chars.
           - thread_replies: 2-4 follow-up replies (each <= 280 chars).
           - engagement_question: Short, pointed question.
           - metadata: {{ "post_type": "thread", "recommended_post_time": "ISO string", "status": "generated" }}
           
        7. comment_seeding_pack:
           - yt_seed_comments: Array of 3 comments.
           - ig_seed_comments: Array of 3 comments.
           - pin_recommendation: Which comment to pin and why.
           - follow_up_timing: "+10 min"
           - creator_reply_templates: {{ "agree": "template text", "neutral": "template text", "calm_disagreement": "template text" }}
           
        8. carousel_asset:
           - slides: 6-8 slides with text (<=12 words), visual_direction, and text_style per slide.
           - caption: Summary for the post.
           - metadata: {{ "status": "generated" }}

        Return valid JSON with these keys. No markdown blocks.
        """

    def _get_mock_package_data(self, cluster_id):
        return {
            "canonical": {
                "secondary_topic": "Federal Oversight",
                "core_thesis": f"The handling of {cluster_id} shows a total lack of transparency."
            },
            "facebook_page_post": {
                "post_body": f"Look, we've seen this before. {cluster_id} is a mess because nobody wants to take responsibility. We checked the records. The numbers don't lie. Canadians deserve better than these half-measures.",
                "headlines": [f"The {cluster_id} Cover-up?", f"Hans Says: Enough with {cluster_id}", "Accountability Now"],
                "cta": "What do you think? Let's hear it below.",
                "pinned_comment": "Keep it civil, keep it factual.",
                "distribution_safe_version": f"Oversight on {cluster_id} requires immediate attention.",
                "metadata": { "recommended_post_time": "2024-03-20T19:30:00Z", "timezone": "America/Toronto", "post_intent": "accountability", "status": "mock" }
            },
            "facebook_group_post": {
                "post_body": f"Quick question for the group: How has the {cluster_id} situation affected your local community? We're looking into the lack of federal response.",
                "discussion_prompt": "We want to hear your personal stories.",
                "safety_notes": "Avoid partisan labels, focus on policy impact.",
                "metadata": { "group_safe_score": 0.85, "recommended_delay": "+45 min", "status": "mock" }
            },
            "instagram_reel": {
                "reel_script": [{"beat": "0:00", "text": "Fed up?"}, {"beat": "0:02", "text": f"{cluster_id} is breaking."}],
                "on_screen_text": ["Fed up?", "Oversight Failed", "Demand Better"],
                "caption": "No more excuses on this one. Link in bio for the full data.",
                "hashtags": ["#CanadaPolitics", "#HansSays", f"#{cluster_id.replace(' ', '')}"],
                "seed_comment": "Is it time for a change?",
                "metadata": { "audio_guidance": "voiceover", "recommended_post_time": "2024-03-20T20:30:00Z", "status": "mock" }
            },
            "youtube_short": {
                "shorts_script": "0:00 - They said it was handled.\n0:10 - The data says otherwise.\n0:20 - Demand better.",
                "title": f"The TRUTH about {cluster_id} in Canada",
                "description": "Hans breaks down the latest failures in oversight.",
                "pinned_comment": "Subscribe for more accountability.",
                "metadata": { "retention_hook_used": True, "recommended_post_time": "2024-03-20T21:30:00Z", "status": "mock" }
            },
            "x_post": {
                "primary_post": f"No more excuses on {cluster_id}. The data is clear: oversight failed. Full breakdown coming.",
                "thread_replies": ["Oversight was warned in 2023.", "Action was promised, none taken.", "Canadians are paying the price."],
                "engagement_question": "Who should be held accountable first?",
                "metadata": { "post_type": "thread", "recommended_post_time": "2024-03-20T19:00:00Z", "status": "mock" }
            },
            "comment_seeding_pack": {
                "yt_seed_comments": ["Great info.", "Share this.", "Keep it up."],
                "ig_seed_comments": ["Finally!", "Spot on.", "Need more of this."],
                "pin_recommendation": "Pin the comment asking about policy impact.",
                "follow_up_timing": "+10 min",
                "creator_reply_templates": {
                    "agree": "Spot on. We need more eyes on this.",
                    "neutral": "Fair point, though the data suggests otherwise.",
                    "calm_disagreement": "I hear you, but let's look at the actual outcomes."
                }
            },
            "carousel_asset": {
                "slides": [{"slide": 1, "text": "The Crisis", "visual_direction": "Chart showing decline", "text_style": "Bold Headline"}],
                "caption": "The full story in slides.",
                "metadata": { "status": "mock" }
            }
        }
    def _get_mock_angle_data(self, cluster_id):
        return {
            "angles": [
                {"type": "Critical", "content": f"The government's approach to {cluster_id} is purely reactive."},
                {"type": "Comparative", "content": f"Unlike peer nations, Canada's {cluster_id} strategy lacks clear benchmarks."},
                {"type": "Accountability", "content": f"Who is signing off on these {cluster_id} decisions?"}
            ],
            "facebook_post": f"Look, we've seen this before. {cluster_id} is a mess because nobody wants to take responsibility."
        }

# For backward compatibility during migration
CommentaryGenerator = ContentEngine
