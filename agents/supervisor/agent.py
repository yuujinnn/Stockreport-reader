"""
Supervisor Agent 구현
사용자 질문 분석 및 워커 에이전트 조정
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain.tools import BaseTool, tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent

from .prompt import SUPERVISOR_PROMPT, FINAL_ANSWER_PROMPT
from ..shared.state import MessagesState


class StockPriceAgentInput(BaseModel):
    """Stock Price Agent 툴 입력 스키마"""
    request: str = Field(
        description="Stock Price Agent에게 전달할 주식 데이터 요청. 종목명과 티커가 포함된 상태"
    )


class SupervisorAgent:
    """
    Supervisor Agent
    사용자의 질문을 분석하고 Stock Price Agent를 조정하여 최종 답변을 생성
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Supervisor Agent 초기화
        
        Args:
            llm: LangChain ChatOpenAI 인스턴스
        """
        self.llm = llm
        
        # Stock Price Agent 인스턴스를 지연 로딩으로 생성
        self._stock_price_agent = None
        
        # Stock Price Agent 툴 정의
        self.stock_price_tool = self._create_stock_price_tool()
        
        # 정확한 날짜 정보 계산
        date_info = self._calculate_date_info()
        
        # tools와 tool_names 정보 추가
        tools_info = self._get_tools_info([self.stock_price_tool])
        
        # 모든 포맷팅 정보 결합
        format_info = {**date_info, **tools_info}
        
        # 프롬프트 포맷팅
        formatted_prompt = SUPERVISOR_PROMPT.format(**format_info)
        
        # LangGraph React Agent 생성 (Tool-calling Supervisor 패턴)
        self.agent = create_react_agent(
            self.llm,
            tools=[self.stock_price_tool],
            prompt=formatted_prompt
        )
    
    def _calculate_date_info(self) -> Dict[str, str]:
        """Python datetime.now()로 정확한 날짜 정보를 계산합니다"""
        today = datetime.now()
        
        # 기본 날짜들
        today_date = today.strftime('%Y%m%d')
        yesterday_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        tomorrow_date = (today + timedelta(days=1)).strftime('%Y%m%d')
        
        # 이번달
        this_month_start = today.replace(day=1).strftime('%Y%m%d')
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        this_month_end = (next_month - timedelta(days=1)).strftime('%Y%m%d')
        
        # 지난달
        if today.month == 1:
            last_month_start = today.replace(year=today.year - 1, month=12, day=1).strftime('%Y%m%d')
            this_month_first = today.replace(day=1)
            last_month_end = (this_month_first - timedelta(days=1)).strftime('%Y%m%d')
        else:
            last_month_start = today.replace(month=today.month - 1, day=1).strftime('%Y%m%d')
            this_month_first = today.replace(day=1)
            last_month_end = (this_month_first - timedelta(days=1)).strftime('%Y%m%d')
        
        # 다음달
        next_month_start = next_month.strftime('%Y%m%d')
        if next_month.month == 12:
            next_next_month = next_month.replace(year=next_month.year + 1, month=1, day=1)
        else:
            next_next_month = next_month.replace(month=next_month.month + 1, day=1)
        next_month_end = (next_next_month - timedelta(days=1)).strftime('%Y%m%d')
        
        # 올해/작년
        this_year_start = today.replace(month=1, day=1).strftime('%Y%m%d')
        this_year_end = today.replace(month=12, day=31).strftime('%Y%m%d')
        last_year_start = today.replace(year=today.year - 1, month=1, day=1).strftime('%Y%m%d')
        last_year_end = today.replace(year=today.year - 1, month=12, day=31).strftime('%Y%m%d')
        
        return {
            'today_date': today_date,
            'yesterday_date': yesterday_date,
            'tomorrow_date': tomorrow_date,
            'this_month_start': this_month_start,
            'this_month_end': this_month_end,
            'last_month_start': last_month_start,
            'last_month_end': last_month_end,
            'next_month_start': next_month_start,
            'next_month_end': next_month_end,
            'this_year_start': this_year_start,
            'this_year_end': this_year_end,
            'last_year_start': last_year_start,
            'last_year_end': last_year_end,
            'current_year': str(today.year),
            'last_year': str(today.year - 1)
        }
    
    def _get_tools_info(self, tools: List[BaseTool]) -> Dict[str, str]:
        """tools 정보를 prompt에 사용할 수 있는 형태로 변환합니다"""
        # tools 설명 생성
        tools_desc = []
        tool_names = []
        
        for tool in tools:
            tool_names.append(tool.name)
            tool_desc = f"- **{tool.name}**: {tool.description}"
            tools_desc.append(tool_desc)
        
        return {
            'tools': '\n'.join(tools_desc),
            'tool_names': ', '.join(tool_names)
        }
    
    @property
    def stock_price_agent(self):
        """Stock Price Agent 인스턴스를 지연 로딩합니다 (순환 import 방지)"""
        if self._stock_price_agent is None:
            from ..stock_price_agent.agent import StockPriceAgent
            self._stock_price_agent = StockPriceAgent(self.llm)
        return self._stock_price_agent
    
    def _create_stock_price_tool(self) -> BaseTool:
        """실제 Stock Price Agent를 호출하는 툴을 생성합니다"""
        
        @tool("call_stock_price_agent", args_schema=StockPriceAgentInput)
        def call_stock_price_agent(request: str) -> str:
            """
            Stock Price Agent를 호출하여 주식 데이터를 조회합니다.
            사용자의 요청을 그대로 전달합니다.
            
            Args:
                request: 주식 데이터 요청 (종목명, 티커, 기간, 차트 유형, 분석 목적 포함)
                
            Returns:
                str: Stock Price Agent의 응답
            """
            try:
                print(f"📝 Stock Price Agent 요청: {request}")
                
                # 실제 Stock Price Agent 호출 (Tool-calling Supervisor 패턴)
                stock_messages = [HumanMessage(content=request)]
                stock_state = MessagesState(
                    messages=stock_messages,
                    user_query=request,
                    extracted_info=None,
                    stock_data=None,
                    error=None,
                    metadata={"source": "supervisor_tool_call"}
                )
                
                # Stock Price Agent 실행
                result_state = self.stock_price_agent.invoke(stock_state)
                
                # 결과 추출
                result_messages = result_state.get("messages", [])
                if result_messages:
                    final_response = result_messages[-1].content
                    return final_response
                else:
                    return "Stock Price Agent에서 응답을 받지 못했습니다."
                    
            except Exception as e:
                return f"Stock Price Agent 호출 중 오류 발생: {str(e)}"
        
        return call_stock_price_agent
    
    def invoke(self, state: MessagesState) -> Dict[str, Any]:
        """
        Supervisor Agent를 실행합니다 (LangGraph Tool-calling Supervisor 패턴)
        
        Args:
            state: 현재 상태
            
        Returns:
            Dict: 업데이트된 상태
        """
        try:
            # LangGraph prebuilt create_react_agent 실행
            result = self.agent.invoke({"messages": state["messages"]})
            
            # 결과에서 메시지 추출
            new_messages = result.get("messages", [])
            
            # 메시지 상태 업데이트
            updated_state = state.copy()
            updated_state["messages"] = new_messages
            
            # 메타데이터 업데이트
            if updated_state["metadata"] is None:
                updated_state["metadata"] = {}
            updated_state["metadata"]["supervisor_processed"] = True
            updated_state["metadata"]["total_messages"] = len(new_messages)
            
            return updated_state
            
        except Exception as e:
            # 오류 처리
            error_message = f"Supervisor Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 