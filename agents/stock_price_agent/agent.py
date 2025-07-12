"""
Stock Price Agent 구현
키움증권 REST API를 통한 주식 데이터 조회
LangGraph 공식 패턴 적용 - 표준 Sub-agent 구현 (OpenAI 전용)
"""

import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from .prompt import STOCK_PRICE_AGENT_PROMPT
from .tools import get_stock_price_tools
from .data_manager import get_data_manager
from ..shared.state import MessagesState


class StockPriceAgent:
    """
    Stock Price Agent (LangGraph 공식 Sub-agent 패턴)
    키움증권 API를 통한 주식 데이터 조회 및 분석
    Supervisor에서 tool로 호출되는 표준 Sub-agent (OpenAI 전용)
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Stock Price Agent 초기화
        
        Args:
            llm: LangChain ChatOpenAI 인스턴스
        """
        self.llm = llm
        self.tools = get_stock_price_tools()
        
        # 사용 중인 모델 정보 출력
        model_info = self._get_model_info(llm)
        print(f"🤖 Stock Price Agent 초기화: {model_info}")
        
        # 데이터 매니저 초기화 (data 폴더 새로 생성)
        self.data_manager = get_data_manager()
        print("📁 Stock Price Agent 데이터 매니저 초기화 완료")
        
        # tools와 tool_names 정보 추가
        tools_info = self._get_tools_info(self.tools)
        
        # 프롬프트 포맷팅
        formatted_prompt = STOCK_PRICE_AGENT_PROMPT.format(**tools_info)
        
        # LangGraph React Agent 생성 (표준 Sub-agent)
        # OpenAI 사용
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=formatted_prompt
        )
    
    def _get_model_info(self, llm) -> str:
        """사용 중인 모델 정보를 반환합니다"""
        try:
            model_name = getattr(llm, 'model_name', None) or getattr(llm, 'model', 'Unknown')
            llm_class = llm.__class__.__name__
            
            if 'OpenAI' in llm_class:
                return f"OpenAI ({model_name})"
            else:
                return f"{llm_class} ({model_name})"
        except:
            return f"{llm.__class__.__name__}"
    
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
    
    def invoke(self, state: MessagesState) -> Dict[str, Any]:
        """
        Stock Price Agent를 실행합니다 (표준 LangGraph Sub-agent 패턴)
        
        Args:
            state: 현재 상태
            
        Returns:
            Dict: 업데이트된 상태
        """
        try:
            # 표준 LangGraph agent invoke
            result = self.agent.invoke({"messages": state["messages"]})
            
            # 결과에서 최종 응답 추출
            result_messages = result.get("messages", [])
            if result_messages:
                final_response = result_messages[-1].content
                
                # 데이터 요약 정보 추가
                data_summary = self.data_manager.get_data_summary()
                summary_text = f"\n\n📊 데이터 처리 요약:\n• 저장된 파일: {data_summary['filtered_files']}개\n• 총 크기: {data_summary['total_size_mb']}MB"
                final_response += summary_text
                
                # 최종 메시지 업데이트
                result_messages[-1].content = final_response
            
            # 메시지 상태 업데이트 (표준 방식)
            updated_state = state.copy()
            updated_state["messages"] = result_messages
            
            # 메타데이터 업데이트
            if updated_state["metadata"] is None:
                updated_state["metadata"] = {}
            updated_state["metadata"]["stock_price_processed"] = True
            updated_state["metadata"]["api_calls_made"] = len(result_messages)
            
            # 데이터 파일 정보 추가
            data_summary = self.data_manager.get_data_summary()
            updated_state["metadata"]["data_files_created"] = data_summary['filtered_files']
            
            return updated_state
            
        except Exception as e:
            # 오류 처리 (표준 방식)
            error_message = f"Stock Price Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 