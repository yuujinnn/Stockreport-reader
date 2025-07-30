"""
ChatClovaX Stock Price Agent
Simplified LangGraph implementation using create_react_agent
"""

from typing import List
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from .prompt import DART_AGENT_PROMPT
from .tools import get_stock_tools
from langchain_naver import ChatClovaX

class DartAgent:
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
        self.tools = get_stock_tools()
    
        
        # Create LangGraph React Agent with enhanced reasoning
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=DART_AGENT_PROMPT
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
    
def run_agent(user_query: str) -> str:
    agent = DartAgent()
    return agent.run(user_query)