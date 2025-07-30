"""
SearchAgent implementation using ChatClovaX and LangGraph
Autonomous search agent with Tavily web search and enhanced Naver News capabilities
"""

import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_naver import ChatClovaX
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv("secrets/.env")
load_dotenv("backend/secrets/.env")

from .prompt import SEARCH_AGENT_SYSTEM_PROMPT
from .tools import get_search_tools
from .naver_api import get_naver_api


class SearchAgent:
    """
    Search Agent using ChatClovaX and LangGraph
    Autonomous agent with web search and Korean news capabilities
    """
    
    def __init__(self):
        """Initialize the agent with ChatClovaX model and search tools"""
        
        # Initialize ChatClovaX model (HCX-005)
        self.llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,  # Sufficient for comprehensive analysis
            temperature=0.3,  # Balanced for reasoning and creativity
        )
        
        # Get search tools
        self.tools = get_search_tools()
        
        # Initialize APIs to verify credentials
        try:
            # Verify Naver API connection
            self.naver_api = get_naver_api()
            print(f"✅ Naver News API connection verified")
            
            # Verify Tavily API (environment variable check)
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                print(f"✅ Tavily API key found")
            else:
                print(f"⚠️ Tavily API key not found - web search may be limited")
                
        except Exception as e:
            print(f"❌ API connection error: {e}")
            raise
        
        # Create LangGraph React Agent with enhanced reasoning
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=SEARCH_AGENT_SYSTEM_PROMPT
        )
        
        print(f"🔍 SearchAgent initialized with ChatClovaX HCX-005")
        print(f"🛠️ Tools available: {[tool.name for tool in self.tools]}")
        print(f"🚀 Ready for autonomous search and analysis")
    
    def run(self, user_query: str) -> str:
        """
        Main entry point for the agent
        
        Args:
            user_query: User's search request or question
            
        Returns:
            str: Agent's comprehensive response with search results and analysis
        """
        try:
            print(f"🔎 Processing search query: {user_query}")
            
            # Invoke the agent with autonomous reasoning - no pre-processing or tool selection
            result = self.agent.invoke({"messages": [HumanMessage(content=user_query)]})
            
            # Extract final response
            if result and "messages" in result:
                messages = result["messages"]
                if messages:
                    final_message = messages[-1]
                    if hasattr(final_message, 'content'):
                        print(f"✅ Search and analysis completed")
                        return final_message.content
            
            return "검색 및 분석을 완료할 수 없습니다. 다시 시도해주세요."
            
        except Exception as e:
            error_msg = f"검색 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # Test Naver API connection
            test_result = self.naver_api.search_news("테스트", max_count=1)
            naver_status = "connected" if test_result else "error"
        except:
            naver_status = "disconnected"
        
        # Check Tavily API key
        tavily_status = "configured" if os.getenv("TAVILY_API_KEY") else "not_configured"
        
        return {
            "agent_initialized": True,
            "llm_model": "ChatClovaX HCX-005",
            "tools_count": len(self.tools),
            "available_tools": self.get_available_tools(),
            "naver_api_status": naver_status,
            "tavily_api_status": tavily_status,
            "agent_type": "SearchAgent",
            "capabilities": [
                "Web Search (Tavily)",
                "Korean News Search by Relevance", 
                "Korean News Search by Date",
                "Content Crawling",
                "Autonomous Tool Selection",
                "Comprehensive Analysis"
            ]
        }


def run_search_agent(user_query: str) -> str:
    """
    Public entry point function for running the search agent
    
    Args:
        user_query: User's search request
        
    Returns:
        str: Agent's response with search results and analysis
    """
    agent = SearchAgent()
    return agent.run(user_query)


# Backward compatibility
def run_news_agent(user_query: str) -> str:
    """
    Backward compatibility function - redirects to SearchAgent
    
    Args:
        user_query: User's request
        
    Returns:
        str: Agent's response
    """
    print("⚠️ Redirecting to SearchAgent (NewsAgent is now SearchAgent)")
    return run_search_agent(user_query) 