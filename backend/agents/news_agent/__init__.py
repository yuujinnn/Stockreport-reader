"""
Search Agent Package
ChatClovaX-based autonomous search agent with comprehensive search capabilities
"""

from .agent import SearchAgent, run_search_agent, run_news_agent
from .tools import get_search_tools
from .naver_api import NaverNewsAPI, get_naver_api
from .prompt import SEARCH_AGENT_SYSTEM_PROMPT

__all__ = [
    # Main agent
    "SearchAgent",
    "run_search_agent",
    "run_news_agent",  # Backward compatibility
    
    # Tools
    "get_search_tools",
    
    # API client
    "NaverNewsAPI", 
    "get_naver_api",
    
    # Prompt
    "SEARCH_AGENT_SYSTEM_PROMPT"
] 