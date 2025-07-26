"""
Naver News API client for NewsAgent
Simplified and optimized for LangGraph Agent integration
"""

import os
import json
import requests
import time
from typing import List, Dict, Optional
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables from multiple possible locations
load_dotenv()  # Load from current directory
load_dotenv("secrets/.env")  # Load from secrets directory
load_dotenv("backend/secrets/.env")  # Load from backend/secrets directory


class NaverNewsAPI:
    """Naver News API client with rate limiting and error handling"""
    
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set in environment variables")
    
    def search_news(self, query: str, max_count: int = 30, sort: str = "sim") -> List[Dict]:
        """
        Search Naver News with given query
        
        Args:
            query: Search query string
            max_count: Maximum number of articles to return (default: 30)
            sort: Sort type - 'sim' (similarity) or 'date' (default: 'sim')
            
        Returns:
            List[Dict]: List of news articles with title, link, description, pubDate
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        results = []
        start = 1
        
        try:
            while len(results) < max_count and start < 1000:
                # Build URL with parameters
                params = {
                    "query": query,
                    "display": min(100, max_count - len(results)),
                    "start": start,
                    "sort": sort
                }
                
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
                
                if response.status_code != 200:
                    print(f"❌ Naver News API error: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break
                
                # Filter for Naver News only and clean data
                for item in items:
                    if "news.naver.com" in item.get("link", ""):
                        article = {
                            "title": self._clean_html_tags(item.get("title", "")),
                            "link": item.get("link", ""),
                            "description": self._clean_html_tags(item.get("description", "")),
                            "pubDate": item.get("pubDate", "")
                        }
                        results.append(article)
                        
                        if len(results) >= max_count:
                            break
                
                start += 100
                time.sleep(0.2)  # Rate limiting
                
        except Exception as e:
            print(f"❌ Error searching Naver News: {e}")
            return []
        
        print(f"📰 Found {len(results)} news articles for query: {query}")
        return results[:max_count]
    
    def _clean_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Remove HTML tags like <b>, </b>, etc.
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Replace HTML entities
        clean_text = clean_text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return clean_text.strip()


# Global API instance
_naver_api = None

def get_naver_api() -> NaverNewsAPI:
    """Get global Naver News API instance"""
    global _naver_api
    if _naver_api is None:
        _naver_api = NaverNewsAPI()
    return _naver_api 