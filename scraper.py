from newspaper import Article
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional

def scrape_article(url):
    """
    Scrapes an article from the given URL.
    
    Args:
        url (str): URL of the article to scrape
        
    Returns:
        dict: Dictionary containing article title, text, publish date, and URL
    """
    article = Article(url)
    article.download()
    article.parse()
    return {
        'title': article.title,
        'text': article.text,
        'publish_date': article.publish_date,
        'url': url
    }

def get_top_stories(section, api_key):
    """
    Gets top stories from NYT API for a specific section.
    
    Args:
        section (str): Section name (world, technology, science, etc.)
        api_key (str): NYT API key
        
    Returns:
        list: List of articles or None if request fails
    """
    url = f"https://api.nytimes.com/svc/topstories/v2/{section}.json"
    params = {'api-key': api_key}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return None

def get_all_articles(api_key):
    """
    Gets top stories from multiple sections.
    
    Args:
        api_key (str): NYT API key
        
    Returns:
        dict: Dictionary with sections as keys and lists of articles as values
    """
    sections = ['world', 'technology', 'science', 'health', 'business']

    all_articles = {}
    for section in sections:
        articles = get_top_stories(section, api_key)
        if articles:
            all_articles[section] = [{
                'title': article['title'],
                'url': article['url'],
                'published_date': article['published_date'],
                'abstract': article['abstract'],
                'section': section
            } for article in articles]

    return all_articles