"""
Supervisor Agent 구현 (ChatClovaX + langgraph-supervisor)
LangGraph 공식 Supervisor 패턴 적용
"""

import os
from typing import Dict, Any, List, Annotated
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langchain_naver import ChatClovaX
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

from .prompt import SUPERVISOR_PROMPT_CLOVAX
from ..shared.state import MessagesState


class SupervisorAgent:
    """
    Supervisor Agent using ChatClovaX and langgraph-supervisor
    """
    
    def __init__(self):
        """
        Initialize Supervisor Agent with ChatClovaX
        """
        # Initialize ChatClovaX for supervisor
        self.supervisor_llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,
            temperature=0.1,  # Slightly higher for better coordination
        )
        
        # Import and initialize Stock Price Agent
        from ..stock_price_agent.agent import StockPriceAgent
        self.stock_price_agent = StockPriceAgent()
        
        ################################################
        # Import and initialize Search Agent (formerly News Agent)
        from ..news_agent.agent import SearchAgent
        self.search_agent = SearchAgent()
        ################################################
        
        # Get formatted prompt with dates
        self.formatted_prompt = self._format_prompt_with_dates()
        
        # ChatClovaX는 langgraph-supervisor와 호환성 문제가 있으므로 수동 구현 사용
        print("🔧 ChatClovaX 호환성을 위해 수동 Supervisor 구현 사용")
        self.supervisor = None
        self._create_manual_supervisor()
    
    def _format_prompt_with_dates(self) -> str:
        """Format prompt with current date information"""
        today = datetime.now()
        
        # Calculate date ranges
        date_info = {
            'today_date': today.strftime('%Y%m%d'),
            'yesterday_date': (today - timedelta(days=1)).strftime('%Y%m%d'),
            'tomorrow_date': (today + timedelta(days=1)).strftime('%Y%m%d'),
            'this_month_start': today.replace(day=1).strftime('%Y%m%d'),
            'this_month_end': self._get_month_end(today).strftime('%Y%m%d'),
            'last_month_start': self._get_last_month_start(today).strftime('%Y%m%d'),
            'last_month_end': (today.replace(day=1) - timedelta(days=1)).strftime('%Y%m%d'),
            'next_month_start': self._get_next_month_start(today).strftime('%Y%m%d'),
            'next_month_end': self._get_next_month_end(today).strftime('%Y%m%d'),
            'this_year_start': today.replace(month=1, day=1).strftime('%Y%m%d'),
            'this_year_end': today.replace(month=12, day=31).strftime('%Y%m%d'),
            'last_year_start': today.replace(year=today.year-1, month=1, day=1).strftime('%Y%m%d'),
            'last_year_end': today.replace(year=today.year-1, month=12, day=31).strftime('%Y%m%d'),
            'current_year': str(today.year),
            'last_year': str(today.year - 1)
        }
        
        return SUPERVISOR_PROMPT_CLOVAX.format(**date_info)
    
    def _get_month_end(self, date):
        """Get the last day of the month"""
        if date.month == 12:
            next_month = date.replace(year=date.year + 1, month=1, day=1)
        else:
            next_month = date.replace(month=date.month + 1, day=1)
        return next_month - timedelta(days=1)
    
    def _get_last_month_start(self, date):
        """Get the first day of last month"""
        if date.month == 1:
            return date.replace(year=date.year - 1, month=12, day=1)
        else:
            return date.replace(month=date.month - 1, day=1)
    
    def _get_next_month_start(self, date):
        """Get the first day of next month"""
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1)
        else:
            return date.replace(month=date.month + 1, day=1)
    
    def _get_next_month_end(self, date):
        """Get the last day of next month"""
        next_month_start = self._get_next_month_start(date)
        return self._get_month_end(next_month_start)
    
    def _create_manual_supervisor(self):
        """Create manual supervisor if langgraph-supervisor fails"""
        from langgraph.graph import StateGraph, START, END
        from langchain_core.tools import tool
        from langgraph.types import Command
        from langgraph.prebuilt import InjectedState
        from typing import Any
        
        # Create handoff tool for Stock Price Agent
        @tool("call_stock_price_agent")
        def call_stock_price_agent(
            request: str,
            state: Annotated[Dict[str, Any], InjectedState]
        ) -> str:
            """
            Call Stock Price Agent for stock data analysis
            
            Args:
                request: The stock analysis request
                state: Current graph state (injected automatically)
            """
            try:
                print(f"📝 Calling Stock Price Agent: {request}")
                
                # Call Stock Price Agent
                result = self.stock_price_agent.run(request)
                return result
                
            except Exception as e:
                return f"Error calling Stock Price Agent: {str(e)}"
        
        ########################################################################################
        # Create handoff tool for Search Agent (comprehensive search capabilities)
        @tool("call_search_agent")
        def call_search_agent(
            request: str,
            state: Annotated[Dict[str, Any], InjectedState]
        ) -> str:
            """
            Call Search Agent for comprehensive search, news analysis, and web research
            
            Args:
                request: The search/analysis request (can be web search, Korean news, or combined)
                state: Current graph state (injected automatically)
            """
            try:
                print(f"🔍 Calling Search Agent: {request}")
                
                # Call Search Agent with enhanced capabilities
                result = self.search_agent.run(request)
                return result
                
            except Exception as e:
                return f"Error calling Search Agent: {str(e)}"
        ########################################################################################
        
        # Create supervisor agent with handoff tools (name 파라미터 제거 - ChatClovaX 호환성)
        self.supervisor_agent = create_react_agent(
            self.supervisor_llm,
            tools=[call_stock_price_agent, call_search_agent], ########################################################################################
            prompt=self.formatted_prompt
        )
        
        # Create simple graph
        workflow = StateGraph(MessagesState)
        workflow.add_node("supervisor", self.supervisor_agent)
        workflow.add_edge(START, "supervisor")
        workflow.add_edge("supervisor", END)
        
        self.supervisor = workflow.compile()
        
        print("🔧 Manual supervisor implementation created successfully")
    
    def invoke(self, state: MessagesState) -> Dict[str, Any]:
        """
        Invoke the supervisor agent
        
        Args:
            state: Current state with messages
            
        Returns:
            Dict: Updated state
        """
        try:
            if self.supervisor is None:
                raise ValueError("Supervisor not initialized")
            
            # Invoke supervisor
            result = self.supervisor.invoke({"messages": state["messages"]})
            
            # Update state
            updated_state = state.copy()
            updated_state["messages"] = result.get("messages", state["messages"])
            
            # Add metadata
            if updated_state["metadata"] is None:
                updated_state["metadata"] = {}
            updated_state["metadata"]["supervisor_processed"] = True
            updated_state["metadata"]["pattern"] = "langgraph_supervisor"
            
            return updated_state
            
        except Exception as e:
            error_message = f"Supervisor Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 