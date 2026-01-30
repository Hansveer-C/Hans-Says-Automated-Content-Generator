POLITICAL_KEYWORDS = {
    "immigration": ["immigration", "migrant", "refugee", "border", "visa", "citizenship"],
    "elections": ["election", "vote", "poll", "ballot", "campaign", "candidate", "voter"],
    "policy": ["policy", "legislation", "bill", "act", "regulation", "reform", "budget"],
    "leaders": [
        "Trudeau", "Poilievre", "Jagmeet", "Modi", "Rahul Gandhi", 
        "Amit Shah", "Biden", "Harris", "Trump"
    ],
    "economy": ["economy", "inflation", "tax", "jobs", "gdp", "interest rate", "housing"],
    "international": ["foreign policy", "diplomacy", "treaty", "un", "nato", "geopolitics"]
}

GET_ALL_KEYWORDS = [item for sublist in POLITICAL_KEYWORDS.values() for item in sublist]

RSS_FEEDS = {
    "Canada": {
        "CBC News - Politics": "https://www.cbc.ca/webfeed/rss/rss-politics",
        "Global News - Politics": "https://globalnews.ca/politics/feed/",
        "National Post - Politics": "https://nationalpost.com/category/news/politics/feed/",
        "The Globe and Mail - Politics": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/politics/",
        "The Hill Times - Politics": "https://www.hilltimes.com/feed/"
    },
    "India": {
        "The Hindu - National": "https://www.thehindu.com/news/national/feeder/default.rss",
        "Indian Express - Political Pulse": "https://indianexpress.com/section/political-pulse/feed/",
        "NDTV News - Top Stories": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "Economic Times - Politics": "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1052730654.cms",
        "Times of India - National": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms"
    }
}

# Controversy Analysis Configuration
CONTROVERSIAL_TOPICS = [
    "abortion", "gun control", "capital punishment", "euthanasia", 
    "affirmative action", "climate change denial", "vaccine mandates",
    "khalistan", "kashmir conflict", "caste discrimination", "caa", "nrc",
    "trucker convoy", "freedom convoy", "residential schools"
]

STRONG_LANGUAGE = [
    "fuck", "shit", "damn", "hell", "asshole", "bitch", "bastard",
    "idiot", "traitor", "scum", "thug", "corrupt", "nazi", "fascist",
    "racist", "bigot", "hate"
]
