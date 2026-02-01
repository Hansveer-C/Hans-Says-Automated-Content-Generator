from typing import List, Set
import re
from config import STRONG_LANGUAGE

class FilterService:
    def __init__(self, blacklist_keywords: List[str] = None, whitelist_sources: Set[str] = None):
        self.blacklist = [k.lower() for k in (blacklist_keywords or [])]
        self.blacklist.extend(STRONG_LANGUAGE) # Auto-blacklist extremely strong language from generation
        self.whitelist_sources = whitelist_sources or set()

    def is_eligible(self, title: str, summary: str, source_name: str) -> bool:
        """
        Determines if an item is eligible for ingestion and content generation.
        """
        text = f"{title} {summary or ''}".lower()
        
        # 1. Check Blacklist
        for word in self.blacklist:
            if re.search(rf'\b{re.escape(word)}\b', text):
                return False
        
        # 2. Check source (Optional logic)
        # if self.whitelist_sources and source_name not in self.whitelist_sources:
        #     return False
            
        return True

    def filter_by_used_status(self, items: List, used: bool = False) -> List:
        """
        Filters a list of ContentItems by their used_for_content status.
        """
        return [item for item in items if item.used_for_content == used]

    def jaccard_similarity(self, str1: str, str2: str) -> float:
        """
        Simple Jaccard similarity between two strings based on words.
        """
        words1 = set(re.sub(r'\W+', ' ', str1.lower()).split())
        words2 = set(re.sub(r'\W+', ' ', str2.lower()).split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
