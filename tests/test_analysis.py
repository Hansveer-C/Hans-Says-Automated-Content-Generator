from app.analysis.controversy import ControversyAnalyzer

def test_analyzer():
    analyzer = ControversyAnalyzer()
    
    test_cases = [
        {
            "title": "Government announces new infrastructure project",
            "summary": "The project aims to improve public transport in major cities.",
            "description": "Neutral News"
        },
        {
            "title": "Protests erupt over controversial abortion ban",
            "summary": "Thousands take to the streets to demand rights.",
            "description": "Sensitive Topic"
        },
        {
            "title": "Opposition leader calls Prime Minister a corrupt liar",
            "summary": "He claims the latest policy is a total shit show.",
            "description": "Strong Language + Polarity"
        },
        {
            "title": "Khalistan supporters hold rally in Canada",
            "summary": "The rally was attended by hundreds of people.",
            "description": "Sensitive Regional Topic"
        },
        {
            "title": "I hate this stupid policy so much",
            "summary": "It's a complete disaster and everyone involved is an idiot.",
            "description": "High Negative Sentiment + Strong Language"
        }
    ]

    print(f"{'Description':<30} | {'Score':<5}")
    print("-" * 40)
    for case in test_cases:
        score = analyzer.analyze(case["title"], case["summary"])
        print(f"{case['description']:<30} | {score:<5}")

if __name__ == "__main__":
    test_analyzer()
