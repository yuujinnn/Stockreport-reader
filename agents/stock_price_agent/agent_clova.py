"""
ChatClovaX Stock Price Agent
Simplified LangGraph implementation using create_react_agent
"""

import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_naver import ChatClovaX
from langgraph.prebuilt import create_react_agent

from .prompt_clova import STOCK_PRICE_AGENT_PROMPT
from .tools_clova import get_stock_tools
from .data_manager_clova import get_data_manager
from .utils_clova import format_prompt_with_dates


class StockPriceAgent:
    """
    Simplified Stock Price Agent using ChatClovaX and LangGraph
    """
    
    def __init__(self):
        """Initialize the agent with ChatClovaX model and tools"""
        
        # Initialize ChatClovaX model (HCX-005)
        self.llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,  # Sufficient for tool usage (>= 1024 required)
            temperature=0,  # Lower for more consistent analysis
        )
        
        # Get tools
        self.tools = get_stock_tools()
        
        # Initialize data manager
        self.data_manager = get_data_manager()
        
        # Format prompt with current dates
        formatted_prompt = format_prompt_with_dates(STOCK_PRICE_AGENT_PROMPT)
        
        # Create LangGraph React Agent with date-formatted prompt
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=formatted_prompt
        )
        
        print(f"🤖 Stock Price Agent initialized with ChatClovaX HCX-005")
        print(f"📊 Tools available: {[tool.name for tool in self.tools]}")
        print(f"📅 Prompt formatted with current dates")
    
    def run(self, user_query: str) -> str:
        """
        Main entry point for the agent
        
        Args:
            user_query: User's question about stock data
            
        Returns:
            str: Agent's response with analysis and data
        """
        try:
            # Invoke the agent
            result = self.agent.invoke({"messages": [HumanMessage(content=user_query)]})
            
            # Extract final response
            if result and "messages" in result:
                messages = result["messages"]
                if messages:
                    final_message = messages[-1]
                    if hasattr(final_message, 'content'):
                        return final_message.content
            
            return "I couldn't process your request. Please try asking about specific stock data."
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]


def run_agent(user_query: str) -> str:
    """
    Public entry point function for running the stock price agent
    
    Args:
        user_query: User's question about stock data
        
    Returns:
        str: Agent's response
    """
    agent = StockPriceAgent()
    return agent.run(user_query) 