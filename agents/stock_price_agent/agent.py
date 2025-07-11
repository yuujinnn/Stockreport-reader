"""
Stock Price Agent 구현
키움증권 REST API를 통한 주식 데이터 조회
"""

import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from .prompt import STOCK_PRICE_AGENT_PROMPT
from .tools import get_stock_price_tools
from .data_manager import get_data_manager
from ..shared.state import MessagesState


class StockPriceAgent:
    """
    Stock Price Agent
    키움증권 API를 통한 주식 데이터 조회 및 분석
    """
    
    def __init__(self, llm: ChatOpenAI):
        """
        Stock Price Agent 초기화
        
        Args:
            llm: LangChain ChatOpenAI 인스턴스
        """
        self.llm = llm
        self.tools = get_stock_price_tools()
        
        # 데이터 매니저 초기화 (data 폴더 새로 생성)
        self.data_manager = get_data_manager()
        print("📁 Stock Price Agent 데이터 매니저 초기화 완료")
        
        # tools와 tool_names 정보 추가
        tools_info = self._get_tools_info(self.tools)
        
        # 프롬프트 포맷팅
        formatted_prompt = STOCK_PRICE_AGENT_PROMPT.format(**tools_info)
        
        # LangGraph React Agent 생성
        self.agent = create_react_agent(
            self.llm,
            tools=self.tools,
            prompt=formatted_prompt
        )
    
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
        Stock Price Agent를 실행합니다
        
        Args:
            state: 현재 상태
            
        Returns:
            Dict: 업데이트된 상태
        """
        try:
            messages = state["messages"]
            
            # 마지막 메시지가 AI 메시지이고 tool_calls가 있는지 확인
            if messages and isinstance(messages[-1], AIMessage):
                last_message = messages[-1]
                
                # tool_calls에서 stock_price 관련 호출 찾기
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        if 'stock_price' in tool_call.get('name', '').lower():
                            # Stock Price Agent가 처리할 요청 추출
                            request = tool_call.get('args', {}).get('request', '')
                            
                            if request:
                                # 요청을 HumanMessage로 변환하여 agent에 전달
                                stock_messages = [HumanMessage(content=request)]
                                
                                # LangGraph agent 실행
                                result = self.agent.invoke({"messages": stock_messages})
                                
                                # 결과에서 최종 응답 추출
                                result_messages = result.get("messages", [])
                                if result_messages:
                                    final_response = result_messages[-1].content
                                    
                                    # 데이터 요약 정보 추가
                                    data_summary = self.data_manager.get_data_summary()
                                    summary_text = f"\n\n📊 데이터 처리 요약:\n• 저장된 파일: {data_summary['filtered_files']}개\n• 총 크기: {data_summary['total_size_mb']}MB"
                                    final_response += summary_text
                                    
                                    # ToolMessage로 응답 생성
                                    tool_message = ToolMessage(
                                        content=final_response,
                                        tool_call_id=tool_call.get('id', 'stock_price_call')
                                    )
                                    
                                    # 메시지 상태 업데이트
                                    updated_state = state.copy()
                                    updated_state["messages"] = messages + [tool_message]
                                    
                                    # 메타데이터 업데이트
                                    if updated_state["metadata"] is None:
                                        updated_state["metadata"] = {}
                                    updated_state["metadata"]["stock_price_processed"] = True
                                    updated_state["metadata"]["api_calls_made"] = len(result_messages)
                                    updated_state["metadata"]["data_files_created"] = data_summary['filtered_files']
                                    
                                    return updated_state
            
            # 직접 호출된 경우 (테스트용)
            elif messages and isinstance(messages[-1], HumanMessage):
                # LangGraph agent 실행
                result = self.agent.invoke({"messages": messages})
                
                # 메시지 상태 업데이트
                updated_state = state.copy()
                updated_state["messages"] = result.get("messages", messages)
                
                return updated_state
            
            # 기타 경우 - 상태 그대로 반환
            return state
            
        except Exception as e:
            # 오류 처리
            error_message = f"Stock Price Agent 처리 중 오류 발생: {str(e)}"
            
            # ToolMessage로 오류 응답 (tool_call이 있는 경우)
            if messages and isinstance(messages[-1], AIMessage):
                last_message = messages[-1]
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    tool_call = last_message.tool_calls[0]  # 첫 번째 tool_call 사용
                    error_tool_message = ToolMessage(
                        content=error_message,
                        tool_call_id=tool_call.get('id', 'error_call')
                    )
                    
                    updated_state = state.copy()
                    updated_state["messages"] = messages + [error_tool_message]
                    updated_state["error"] = str(e)
                    
                    return updated_state
            
            # 일반 AI 메시지로 오류 응답
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 