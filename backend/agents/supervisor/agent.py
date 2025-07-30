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

from .prompt import SUPERVISOR_PROMPT
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
        from ..search_agent.agent import SearchAgent
        self.search_agent = SearchAgent()
        
        # Import and initialize DART Agent
        from ..dart_agent.agent import DartAgent
        self.dart_agent = DartAgent()
        ################################################
        
        # ChatClovaX는 langgraph-supervisor와 호환성 문제가 있으므로 수동 구현 사용
        print("🔧 ChatClovaX 호환성을 위해 수동 Supervisor 구현 사용")
        self.supervisor = None
        self._create_manual_supervisor()
    
    def _format_prompt_with_dates(self, user_query: str = "사용자 질문이 제공되지 않았습니다", context: str = "") -> str:
        """Format prompt with current date information, tool information, and context"""
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
            'last_year': str(today.year - 1),
            # Tool-related variables (동적 생성)
            'tool_names': ', '.join([tool.name for tool in getattr(self, 'tools', [])]),
            'user_query': user_query,
            'tools': '\n'.join([f"- {tool.name}: {tool.description}" for tool in getattr(self, 'tools', [])]),
            # Context information
            'context': context if context.strip() else "인용된 문서가 없습니다."
        }
        
        return SUPERVISOR_PROMPT.format(**date_info)
    
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
        
        # Initialize tools list
        self.tools = []
        
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
                error_msg = f"Error calling Stock Price Agent: {str(e)}"
                print(f"❌ {error_msg}")
                # 재시도 로직 (지수 백오프)
                import time
                for retry_count in range(2):
                    try:
                        print(f"🔄 Retrying Stock Price Agent call (attempt {retry_count + 1}/2)")
                        time.sleep(2 ** retry_count)  # 1초, 2초 백오프
                        result = self.stock_price_agent.run(request)
                        return result
                    except Exception as retry_e:
                        print(f"❌ Retry {retry_count + 1} failed: {retry_e}")
                        continue
                
                return f"Stock Price Agent 호출에 실패했습니다. Kiwoom API 접근에 문제가 있을 수 있습니다. 오류: {str(e)}"
        
        # Add to tools list
        self.tools.append(call_stock_price_agent)
        
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
                error_msg = f"Error calling Search Agent: {str(e)}"
                print(f"❌ {error_msg}")
                # 재시도 로직 (지수 백오프)
                import time
                for retry_count in range(2):
                    try:
                        print(f"🔄 Retrying Search Agent call (attempt {retry_count + 1}/2)")
                        time.sleep(2 ** retry_count)  # 1초, 2초 백오프
                        result = self.search_agent.run(request)
                        return result
                    except Exception as retry_e:
                        print(f"❌ Retry {retry_count + 1} failed: {retry_e}")
                        continue
                
                return f"Search Agent 호출에 실패했습니다. 웹 검색 또는 뉴스 API 접근에 문제가 있을 수 있습니다. 오류: {str(e)}"
        
        # Add to tools list
        self.tools.append(call_search_agent)
        
        # Create handoff tool for DART Agent
        @tool("call_dart_agent")
        def call_dart_agent(
            request: str,
            state: Annotated[Dict[str, Any], InjectedState]
        ) -> str:
            """
            Call DART Agent for corporate disclosure and financial report analysis
            
            Args:
                request: The DART analysis request (corporate filings, financial reports, disclosure documents)
                state: Current graph state (injected automatically)
            """
            try:
                print(f"📈 Calling DART Agent: {request}")
                
                # Call DART Agent
                result = self.dart_agent.run(request)
                return result
                
            except Exception as e:
                error_msg = f"Error calling DART Agent: {str(e)}"
                print(f"❌ {error_msg}")
                # 재시도 로직 (지수 백오프)
                import time
                for retry_count in range(2):
                    try:
                        print(f"🔄 Retrying DART Agent call (attempt {retry_count + 1}/2)")
                        time.sleep(2 ** retry_count)  # 1초, 2초 백오프
                        result = self.dart_agent.run(request)
                        return result
                    except Exception as retry_e:
                        print(f"❌ Retry {retry_count + 1} failed: {retry_e}")
                        continue
                
                return f"DART Agent 호출에 실패했습니다. 전자공시 시스템 접근에 문제가 있을 수 있습니다. 오류: {str(e)}"
        
        # Add to tools list
        self.tools.append(call_dart_agent)
        
        # Create supervisor agent with handoff tools (name 파라미터 제거 - ChatClovaX 호환성)
        # 기본 프롬프트로 초기화 (user_query는 실행 시점에서 동적으로 설정)
        default_prompt = self._format_prompt_with_dates("사용자 질문을 기다리는 중입니다...")
        
        self.supervisor_agent = create_react_agent(
            self.supervisor_llm,
            tools=self.tools, 
            prompt=default_prompt
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
            
            # 사용자 질문과 컨텍스트 추출
            user_query = state.get("user_query", "사용자 질문이 제공되지 않았습니다")
            context = state.get("context", "")
            
            # 동적으로 프롬프트 생성 (컨텍스트 포함)
            dynamic_prompt = self._format_prompt_with_dates(user_query, context)
            
            # Create new supervisor agent with updated prompt
            from langgraph.prebuilt import create_react_agent
            updated_supervisor_agent = create_react_agent(
                self.supervisor_llm,
                tools=self.tools, 
                prompt=dynamic_prompt
            )
            
            # Create temporary graph with updated supervisor
            from langgraph.graph import StateGraph, START, END
            temp_workflow = StateGraph(MessagesState)
            temp_workflow.add_node("supervisor", updated_supervisor_agent)
            temp_workflow.add_edge(START, "supervisor")
            temp_workflow.add_edge("supervisor", END)
            temp_supervisor = temp_workflow.compile()
            
            # Invoke updated supervisor
            result = temp_supervisor.invoke({"messages": state["messages"]})
            
            # Update state
            updated_state = state.copy()
            updated_state["messages"] = result.get("messages", state["messages"])
            
            # Add metadata
            if updated_state["metadata"] is None:
                updated_state["metadata"] = {}
            updated_state["metadata"]["supervisor_processed"] = True
            updated_state["metadata"]["pattern"] = "langgraph_supervisor"
            updated_state["metadata"]["context_used"] = bool(context and context.strip())
            
            return updated_state
            
        except Exception as e:
            error_message = f"Supervisor Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 