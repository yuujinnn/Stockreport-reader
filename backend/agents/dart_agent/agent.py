"""
ChatClovaX DART Agent
DART API를 통한 전자공시 보고서 분석 - LangGraph implementation using create_react_agent
"""

from typing import List
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from .prompt import DART_AGENT_PROMPT
from .tools import get_dart_tools
from langchain_naver import ChatClovaX

class DartAgent:
    """
    DART Agent using ChatClovaX and LangGraph
    Autonomous agent with DART API for corporate disclosure analysis
    """
    
    def __init__(self):
        """Initialize the agent with ChatClovaX model and DART tools"""
        
        # Initialize ChatClovaX model (HCX-005)
        self.llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,  # Sufficient for comprehensive analysis
            temperature=0.3,  # Balanced for reasoning and creativity
        )
        
        # Get DART tools
        self.tools = get_dart_tools()

        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=DART_AGENT_PROMPT
        )
        
        print(f"📈 DartAgent initialized with ChatClovaX HCX-005")
        print(f"🛠️ Tools available: {[tool.name for tool in self.tools]}")
        print(f"🚀 Ready for autonomous DART analysis")
    
    def run(self, user_query: str) -> str:
        """
        Main entry point for the agent
        
        Args:
            user_query: User's DART analysis request or question
            
        Returns:
            str: Agent's comprehensive response with DART analysis results
        """
        try:
            print(f"📊 Processing DART analysis query: {user_query}")
            
            # Invoke the agent with autonomous reasoning - no pre-processing or tool selection
            result = self.agent.invoke({"messages": [HumanMessage(content=user_query)]})
            
            # Extract final response
            if result and "messages" in result:
                messages = result["messages"]
                if messages:
                    final_message = messages[-1]
                    if hasattr(final_message, 'content'):
                        print(f"✅ DART analysis completed")
                        return final_message.content
            
            return "DART 분석을 완료할 수 없습니다. 다시 시도해주세요."
            
        except Exception as e:
            error_msg = f"DART 분석 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    

def run_agent(user_query: str) -> str:
    agent = DartAgent()
    return agent.run(user_query)