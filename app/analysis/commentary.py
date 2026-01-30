import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import ContentItem, TopicCommentary

class CommentaryGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def generate_for_cluster(self, db: Session, cluster_id: str) -> Optional[TopicCommentary]:
        """
        Generates 3 commentary angles and a Facebook-ready version for a given cluster.
        """
        # 1. Fetch top items in this cluster
        items = db.query(ContentItem).filter(
            ContentItem.cluster_id == cluster_id
        ).order_by(ContentItem.final_score.desc()).limit(10).all()

        if not items:
            return None

        # 2. Extract context
        context = "\n".join([f"- {item.title}: {item.summary}" for item in items])
        
        data = None
        if self.client:
            try:
                prompt = f"""
                You are a political analyst for 'HansSays', an intelligence engine focusing on Canada and India politics.
                Analyze the following top news items for the topic '{cluster_id}':
                
                {context}
                
                Generate three distinct commentary angles:
                1. Critical: A deep dive into the flaws or risks.
                2. Comparative: Analyzing the situation by comparing Canada's approach vs India's (or vice-versa).
                3. Accountability-focused: Identifying who is responsible and what they should be held to.
                
                Finally, identify the STRONGEST angle and rewrite it as a Facebook-ready post. 
                Facebook Tone Requirements:
                - Plain language (no academic jargon)
                - Short paragraphs
                - Emotionally engaging but "report-safe" (no hate speech or extreme bias)
                - Strong hook
                - Clear stance
                
                Return the result in JSON format:
                {{
                  "angles": [
                    {{"type": "Critical", "content": "..."}},
                    {{"type": "Comparative", "content": "..."}},
                    {{"type": "Accountability", "content": "..."}}
                  ],
                  "strongest_angle_type": "...",
                  "facebook_post": "..."
                }}
                """

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
                print(f"Error calling LLM: {e}")

        # 3. Fallback to mock if LLM failed or wasn't available
        if not data:
            data = self._get_mock_data(cluster_id)
            
        # 4. Save and return
        commentary = TopicCommentary(
            cluster_id=cluster_id,
            angles=data["angles"],
            strongest_angle_html=data["facebook_post"]
        )
        
        db.add(commentary)
        db.commit()
        db.refresh(commentary)
        return commentary

    def _get_mock_data(self, cluster_id: str) -> Dict:
        return {
            "angles": [
                {"type": "Critical", "content": f"The current handling of {cluster_id} is lacking transparency and coordination across various sectors."},
                {"type": "Comparative", "content": f"While Canada is focusing on long-term sustainability, India's rapid development in {cluster_id} provides a stark contrast in pace."},
                {"type": "Accountability", "content": f"Decision makers in the {cluster_id} space must be held accountable for the recent policy shifts that caught many by surprise."}
            ],
            "facebook_post": f"🚨 <b>Is {cluster_id} spinning out of control?</b><br><br>We've been seeing a lot of headlines about {cluster_id} lately, but nobody is asking the hard questions.<br><br>While other countries are moving forward, we seem to be stuck in neutral. It's time for some real accountability.<br><br>What do you think? 👇"
        }
