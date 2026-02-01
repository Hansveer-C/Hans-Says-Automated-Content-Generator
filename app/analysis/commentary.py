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
            angles=data["angles"],
            strongest_angle_html=data["facebook_post"]
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
        ).order_by(ContentItem.final_score.desc()).limit(10).all()

        if not items:
            return None

        context = "\n".join([f"- {item.title}: {item.summary}" for item in items])
        
        # We need the strongest angle first
        commentary = db.query(TopicCommentary).filter(TopicCommentary.cluster_id == cluster_id).order_by(TopicCommentary.generated_at.desc()).first()
        if not commentary:
            commentary = self.generate_commentary_angles(db, cluster_id)

        strongest_angle = commentary.strongest_angle_html # This is a placeholder for the actual text

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
            safe_article=data["safe_article"],
            safe_headlines=data["safe_headlines"],
            safe_cta=data["safe_cta"],
            pinned_comment=data["pinned_comment"],
            x_thread=data.get("x_thread"),
            shorts_script=data.get("shorts_script"),
            reels_script=data.get("reels_script"),
            seeding_pack=data.get("seeding_pack"),
            carousel_slides=data["carousel_slides"],
            visual_directions=data["visual_directions"],
            recommended_post_time=scheduling["time"],
            scheduling_metadata={
                "timezone": scheduling["timezone"],
                "why_this_time_works": scheduling["why"],
                "staggered_offsets": scheduling["staggered_offsets"]
            }
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
        Assigns recommended Facebook posting time using Canadian time zones.
        - Breaking / controversial -> evening prime window
        - Policy-heavy -> lunch window
        
        Includes staggered offsets for other platforms:
        X (Immediate) -> FB (Offset) -> IG (Offset) -> YT (Offset)
        """
        from datetime import datetime, time, timedelta
        
        # Default to today
        now = datetime.now()
        
        # Heuristic: if cluster is "policy" or "student visas" -> Lunch
        is_policy = any(k in cluster_id.lower() for k in ["policy", "student", "economy", "international"])
        
        if is_policy:
            # Lunch window: 12:30 PM
            target_time = time(12, 30)
            why = "Policy-heavy topics perform better in the lunch window when professionals are browsing."
        else:
            # Evening prime: 7:30 PM
            target_time = time(19, 30)
            why = "Controversial or breaking news gains maximum engagement in the evening prime window."
        
        # Schedule for today or tomorrow if time passed
        scheduled_dt = datetime.combine(now.date(), target_time)
        if scheduled_dt < now:
            scheduled_dt += timedelta(days=1)
            
        return {
            "time": scheduled_dt,
            "timezone": "America/Toronto (EST/EDT)",
            "why": why,
            "staggered_offsets": {
                "X": 0,          # X is usually first for breaking news
                "Facebook": 30,  # +30 mins
                "Instagram": 60, # +1 hour
                "YouTube": 120   # +2 hours
            }
        }

    def _get_angle_prompt(self, cluster_id, context):
        return f"""
        Analyze the following top news items for the topic '{cluster_id}':
        {context}
        
        Generate three distinct commentary angles:
        1. Critical: A deep dive into the flaws or risks.
        2. Comparative: Analyzing the situation by comparing Canada's approach vs India's (or vice-versa).
        3. Accountability-focused: Identifying who is responsible and what they should be held to.
        
        Finally, identify the STRONGEST angle and rewrite it as a Facebook-ready post stub. 
        Return in JSON format: {{ "angles": [...], "facebook_post": "..." }}
        """

    def _get_package_prompt(self, cluster_id, context, strongest_angle):
        return f"""
        You are HANS SAYS. Your voice is blunt, Canadian, accountability-focused. Use plain spoken language, short sentences. No hashtags, no slogans.
        
        Topic: {cluster_id}
        Selected Angle: {strongest_angle}
        News Context: {context}
        
        Implement the following steps:
        1. Article Generation: Write a 300-400 word article. Clear stance, conversational, strong hook.
        2. Readability Pass: Ensure 6th-grade reading level.
        3. Facebook Pass: Mobile format, short paragraphs, no bullet points, clean spacing.
        4. Safety Pass: Identify risky claims and reframe them into defensible language without weakening the stance.
        5. Headlines: 3 scroll-stopping headlines (under 12 words).
        6. CTA: 1 engagement CTA.
        7. Pinned Comment: 1-2 sentences inviting debate, not insults.
        8. Visual Media: Extract 6-8 visual beats (under 2s each) and carousel slide text (max 12 words).
        9. X Thread: Generate a 3-4 post thread based on the article. No hashtags.
        10. YouTube Shorts: Write a 30s high-energy script with timestamps and a pinned comment.
        11. Instagram Reels: Write a fast-paced script, catchy caption, and 5 hashtags at the end.
        12. Seeding Pack: 3 recommended seed comments for each platform.
        
        Return the result in JSON:
        {{
          "safe_article": "...",
          "safe_headlines": ["...", "...", "..."],
          "safe_cta": "...",
          "pinned_comment": "...",
          "x_thread": ["Post 1 text", "Post 2 text", "..."],
          "shorts_script": "0:00 - [Hook]...\n0:05 - ...",
          "reels_script": "Visual: ... Audio: ... Caption: ...",
          "seeding_pack": {{ "X": ["..."], "YT": ["..."], "IG": ["..."] }},
          "carousel_slides": [{{ "slide_number": 1, "text": "..." }}, ...],
          "visual_directions": [{{ "slide_number": 1, "direction": "..." }}, ...],
          "core_thesis": "..."
        }}
        """

    def _get_mock_angle_data(self, cluster_id):
        return {
            "angles": [
                {"type": "Critical", "content": f"HANS SAYS: This analysis of '{cluster_id}' exposes significant accountability gaps. The current approach prioritizes PR over policy results."},
                {"type": "Comparative", "content": f"How does Canada's strategy on '{cluster_id}' compare to the rest of the G7? The data suggests we are falling behind on key transparency metrics."},
                {"type": "Accountability", "content": f"Who is actually making the calls on '{cluster_id}'? Without a designated lead, accountability remains a revolving door."}
            ],
            "facebook_post": f"🚨 HANS SAYS: Enough excuses on {cluster_id}. We need names, dates, and clear accountability. Read the full breakdown below. 🚨"
        }

    def _get_mock_package_data(self, cluster_id):
        return {
            "safe_article": f"This is a mock HANS SAYS article about {cluster_id}. It's blunt and Canadian.",
            "safe_headlines": ["Headline 1", "Headline 2", "Headline 3"],
            "safe_cta": "What do you think? Let us know below.",
            "pinned_comment": "Keep it civil, but tell us the truth.",
            "carousel_slides": [{"slide_number": 1, "text": "Slide 1 text"}],
            "visual_directions": [{"slide_number": 1, "direction": "Abstract symbolic visual"}],
            "scheduling_metadata": {"timezone": "America/Toronto", "why": "Evening prime window"}
        }

# For backward compatibility during migration
CommentaryGenerator = ContentEngine
