"""
LangChain tools for SearchAgent
Comprehensive search capabilities including Tavily web search and enhanced Naver News
"""

import json
import requests
from typing import List, Dict, Optional
from langchain.tools import BaseTool
from langchain_naver import ChatClovaX
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()
load_dotenv("secrets/.env")
load_dotenv("backend/secrets/.env")

from .naver_api import get_naver_api


class TavilySearchInput(BaseModel):
    query: str = Field(description="Search query for general web search")
    max_results: int = Field(default=5, description="Maximum number of search results to retrieve")


class NaverNewsRelevanceInput(BaseModel):
    keywords: str = Field(description="Search keywords for Naver News search by relevance")
    max_articles: int = Field(default=10, description="Maximum number of articles to retrieve")


class NaverNewsDateInput(BaseModel):
    keywords: str = Field(description="Search keywords for Naver News search by date")
    max_articles: int = Field(default=10, description="Maximum number of articles to retrieve")


def crawl_content(url: str) -> str:
    """
    Crawl and extract content from a given URL
    
    Args:
        url: URL to crawl content from
        
    Returns:
        Extracted text content or error message
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content length to avoid overwhelming LLM
        return content[:2000] if len(content) > 2000 else content
        
    except Exception as e:
        return f"Content crawling failed: {str(e)}"


class TavilyWebSearchTool(BaseTool):
    name: str = "tavily_web_search"
    description: str = """Comprehensive global web search using Tavily API. BEST FOR: General knowledge questions, international topics, technology trends, research queries, global companies, English-language content, and non-Korean news queries. Use when user asks about world events, scientific topics, foreign companies, or needs broad web-based research. Provides web search results with automatic content crawling for deeper analysis."""
    args_schema: type = TavilySearchInput

    def _run(self, query: str, max_results: int = 10) -> str:
        """
        Perform web search using Tavily API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to retrieve
            
        Returns:
            JSON string of search results with crawled content
        """
        try:
            # Create Tavily search tool instance  
            tavily_tool = TavilySearch(
                max_results=max_results,
                topic="general"
            )
            
            # Perform search
            search_results = tavily_tool.invoke(query)
            
            # TavilySearch returns results in a different format
            # Parse and enhance results with content crawling
            if isinstance(search_results, str):
                # If results are already formatted as string, parse them
                try:
                    results_data = json.loads(search_results)
                    # Handle the case where results might be nested
                    if isinstance(results_data, dict) and 'results' in results_data:
                        results_data = results_data['results']
                except:
                    # If not JSON, treat as plain text
                    results_data = [{"content": search_results, "url": "N/A"}]
            else:
                results_data = search_results if isinstance(search_results, list) else [search_results]
            
            # Enhance results with content crawling
            enhanced_results = []
            for result in results_data[:max_results]:
                enhanced_result = result.copy() if isinstance(result, dict) else {"content": str(result)}
                
                # If URL is available, try to crawl additional content
                if isinstance(result, dict) and "url" in result:
                    crawled_content = crawl_content(result["url"])
                    enhanced_result["crawled_content"] = crawled_content
                
                enhanced_results.append(enhanced_result)
            
            result_summary = {
                "query": query,
                "search_engine": "Tavily",
                "results_count": len(enhanced_results),
                "results": enhanced_results
            }
            
            print(f"🌐 Tavily web search completed: {len(enhanced_results)} results for '{query}'")
            return json.dumps(result_summary, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"❌ Tavily web search error: {str(e)}"
            print(error_msg)
            return json.dumps({"error": error_msg, "query": query}, ensure_ascii=False)


class NaverNewsRelevanceTool(BaseTool):
    name: str = "search_naver_news_by_relevance"
    description: str = """Search Korean Naver News by relevance ranking. BEST FOR: Korean companies, Korean celebrities, Korean politics, domestic Korean issues, or when you need the MOST RELEVANT Korean news articles about a topic (not necessarily the newest). Use when user asks about Korean entities and wants comprehensive coverage sorted by how closely articles match the topic. Results include content crawling for detailed analysis."""
    args_schema: type = NaverNewsRelevanceInput

    def _run(self, keywords: str, max_articles: int = 10) -> str:
        """
        Search Naver News by relevance with content crawling
        
        Args:
            keywords: Search keywords
            max_articles: Maximum number of articles to retrieve
            
        Returns:
            JSON string of news articles with crawled content
        """
        try:
            naver_api = get_naver_api()
            
            # Custom API call for relevance sorting (default)
            client_id = os.getenv("NAVER_CLIENT_ID")
            client_secret = os.getenv("NAVER_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                return "❌ Naver API credentials not found"
            
            # Naver News API call with relevance sorting (default)
            url = f"https://openapi.naver.com/v1/search/news.json?query={quote(keywords)}&display={min(max_articles, 100)}&start=1"
            
            headers = {
                'X-Naver-Client-Id': client_id,
                'X-Naver-Client-Secret': client_secret
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('items', [])
            
            if not articles:
                return f"❌ No news articles found for '{keywords}'"
            
            # Process and enhance articles with content crawling
            enhanced_articles = []
            for article in articles[:max_articles]:
                enhanced_article = {
                    "title": article.get("title", "").replace("<b>", "").replace("</b>", ""),
                    "description": article.get("description", "").replace("<b>", "").replace("</b>", ""),
                    "link": article.get("link", ""),
                    "pubDate": article.get("pubDate", ""),
                    "originallink": article.get("originallink", "")
                }
                
                # Crawl content from the article link
                if enhanced_article["link"]:
                    crawled_content = crawl_content(enhanced_article["link"])
                    enhanced_article["crawled_content"] = crawled_content
                
                enhanced_articles.append(enhanced_article)
            
            result = {
                "keywords": keywords,
                "search_method": "naver_news_by_relevance",
                "total_found": data.get("total", 0),
                "articles_retrieved": len(enhanced_articles),
                "articles": enhanced_articles
            }
            
            print(f"📰 Naver News (relevance) search completed: {len(enhanced_articles)} articles for '{keywords}'")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"❌ Naver News (relevance) search error: {str(e)}"
            print(error_msg)
            return json.dumps({"error": error_msg, "keywords": keywords}, ensure_ascii=False)


class NaverNewsDateTool(BaseTool):
    name: str = "search_naver_news_by_date"
    description: str = """Search Korean Naver News by most recent publication date. BEST FOR: Breaking news, recent events, latest updates, when user specifically asks for 'recent', 'latest', 'today', or 'current' Korean news. Use when freshness/recency of news is more important than relevance. Results are sorted chronologically with newest first. Results include content crawling for detailed analysis."""
    args_schema: type = NaverNewsDateInput

    def _run(self, keywords: str, max_articles: int = 10) -> str:
        """
        Search Naver News by date (most recent first) with content crawling
        
        Args:
            keywords: Search keywords  
            max_articles: Maximum number of articles to retrieve
            
        Returns:
            JSON string of news articles with crawled content
        """
        try:
            # Custom API call for date sorting
            client_id = os.getenv("NAVER_CLIENT_ID")
            client_secret = os.getenv("NAVER_CLIENT_SECRET")
            
            if not client_id or not client_secret:
                return "❌ Naver API credentials not found"
            
            # Naver News API call with date sorting
            url = f"https://openapi.naver.com/v1/search/news.json?query={quote(keywords)}&display={min(max_articles, 100)}&start=1&sort=date"
            
            headers = {
                'X-Naver-Client-Id': client_id,
                'X-Naver-Client-Secret': client_secret
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('items', [])
            
            if not articles:
                return f"❌ No recent news articles found for '{keywords}'"
            
            # Process and enhance articles with content crawling
            enhanced_articles = []
            for article in articles[:max_articles]:
                enhanced_article = {
                    "title": article.get("title", "").replace("<b>", "").replace("</b>", ""),
                    "description": article.get("description", "").replace("<b>", "").replace("</b>", ""),
                    "link": article.get("link", ""),
                    "pubDate": article.get("pubDate", ""),
                    "originallink": article.get("originallink", "")
                }
                
                # Crawl content from the article link
                if enhanced_article["link"]:
                    crawled_content = crawl_content(enhanced_article["link"])
                    enhanced_article["crawled_content"] = crawled_content
                
                enhanced_articles.append(enhanced_article)
            
            result = {
                "keywords": keywords,
                "search_method": "naver_news_by_date",
                "total_found": data.get("total", 0),
                "articles_retrieved": len(enhanced_articles),
                "articles": enhanced_articles
            }
            
            print(f"📅 Naver News (by date) search completed: {len(enhanced_articles)} articles for '{keywords}'")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"❌ Naver News (by date) search error: {str(e)}"
            print(error_msg)
            return json.dumps({"error": error_msg, "keywords": keywords}, ensure_ascii=False)


def get_search_tools():
    """Get list of search tools for SearchAgent"""
    return [
        TavilyWebSearchTool(),
        NaverNewsRelevanceTool(),
        NaverNewsDateTool()
    ] 