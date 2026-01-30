import re
from typing import List, Optional

class TopicClusterer:
    def __init__(self):
        self.clusters = {
            "immigration": [
                "immigration", "border", "migrant", "refugee", "asylum", "visa", 
                "citizenship", "deportation", "undocumented", "h-1b", "pr cards", "citizens", "immigrants"
            ],
            "foreign interference": [
                "interference", "foreign influence", "election meddling", "hacking",
                "disinformation", "propaganda", "espionage", "spying", "cyberattack", "allegations"
            ],
            "religious conflict": [
                "religion", "religious", "faith", "church", "mosque", "temple",
                "sectarian", "blasphemy", "extremism", "fundamentalism", "hindu", "muslim", "sikh", "christian", "jewish", "catholic"
            ],
            "student visas": [
                "student visa", "international student", "study permit", "education visa",
                "university enrollment", "college intake", "study in canada", "student intake"
            ],
            "crime": [
                "crime", "criminal", "violence", "theft", "murder", "assault",
                "policing", "law enforcement", "jail", "prison", "safety", "arrest", "police", "guilty", "suspect"
            ],
            "geopolitics": [
                "geopolitics", "foreign policy", "diplomacy", "international relations",
                "summit", "treaty", "alliance", "sanctions", "conflict", "war",
                "military", "strategic", "modi", "trudeau", "biden", "trump", "china", "russia", "india", "israel", "palestine", "gaza", "ukraine", "nato"
            ]
        }

    def categorize(self, title: str, summary: Optional[str] = "") -> str:
        """
        Categorizes a content item into one of the predefined clusters.
        Returns the cluster name or "other" if no match is found.
        """
        text = f"{title} {summary or ''}".lower()
        
        # Count matches for each cluster
        matches = {}
        for cluster, keywords in self.clusters.items():
            count = 0
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', text):
                    count += 1
            if count > 0:
                matches[cluster] = count
        
        if not matches:
            return "other"
            
        # Return the cluster with the most matches
        return max(matches, key=matches.get)

    def cluster_items(self, items: List) -> List:
        """
        Assigns a cluster_id to each item in the list.
        """
        for item in items:
            item.cluster_id = self.categorize(item.title, item.summary)
        return items
