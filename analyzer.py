import anthropic
import json
from typing import Dict, List
from datetime import datetime
from collections import Counter

class NewsAnalyzer:
    def __init__(self, api_key: str):
        """
        Initialize the NewsAnalyzer with Claude API credentials.
        
        Args:
            api_key (str): Anthropic API key
        """
        self.client = anthropic.Client(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def _extract_key_themes(self, articles: List[Dict]) -> List[str]:
        """
        Extract main themes from a list of articles using Claude.
        
        Args:
            articles (List[Dict]): List of article dictionaries
            
        Returns:
            List[str]: Extracted themes
        """
        # Prepare prompt for Claude
        articles_text = "\n".join([
            f"Title: {article.get('title', '')}\n"
            f"Abstract: {article.get('abstract', '')}\n"
            for article in articles
        ])

        prompt = f"""Analyze these news articles and identify 3-4 key one-word themes. First describe each item in bullet points succinctly, then focus on major trends and patterns:

        {articles_text}

        Please provide the themes in a bullet-point format."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Extract themes from Claude's response
        themes = response.content[0].text.split("\n")
        return [theme.strip("• ").strip() for theme in themes if theme.strip()]

    def analyze_news_data(self, news_data: Dict[str, List[Dict]]) -> Dict:
        """
        Analyze news data and generate insights using Claude API.

        Args:
            news_data (Dict[str, List[Dict]]): Dictionary with sections as keys and lists of articles as values
                Each article should have 'title', 'abstract', 'published_date', and 'url' fields

        Returns:
            Dict: Analysis results including:
                - Article counts per section
                - Key themes per section
                - Recent headlines
                - Timeline analysis
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "sections": {}
        }

        for section, articles in news_data.items():
            if not articles:
                continue

            # Basic statistics
            section_analysis = {
                "article_count": len(articles),
                "recent_headlines": [
                    article["title"] for article in articles
                ],
                "key_themes": self._extract_key_themes(articles),
                "date_range": {
                    "start": min(article["published_date"] for article in articles if article.get("published_date")),
                    "end": max(article["published_date"] for article in articles if article.get("published_date"))
                }
            }

            # Add to main analysis
            analysis["sections"][section] = section_analysis

        return analysis

    def generate_summary_report(self, analysis: Dict) -> str:
        """
        Generate a human-readable summary report from the analysis as if you are an expert on world news from Bloomberg.
        
        The report focuses on new conflicts, risks and opportunities for countries and companies,
        supply and demand changes, and advice for entrepreneurs.

        Args:
            analysis (Dict): Analysis output from analyze_news_data()

        Returns:
            str: Formatted summary report
        """
        prompt = f"""Based on this news analysis data, create a concise summary report highlighting the most important insights:

        {json.dumps(analysis, indent=2)}

        Format the report with sections for:
        1. Overall Coverage Summary
        2. Key Themes by Section
        3. Notable Recent Headlines
        4. Your expert reflection of the current world conditions based on today's news.
        5. Hidden trendes and opportunties for companies.
        """

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text