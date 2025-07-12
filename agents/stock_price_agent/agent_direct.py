"""
ChatClovaX 기반 Direct Stock Price Agent 구현
독립적인 StateGraph 구조로 키움증권 API 데이터 조회
"""

import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_naver import ChatClovaX
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from dotenv import load_dotenv

from .prompt_direct import DIRECT_STOCK_PRICE_AGENT_PROMPT
from .tools_direct import get_direct_stock_price_tools
from .data_manager import get_data_manager
from ..shared.state import MessagesState

# 환경변수 로드
load_dotenv("secrets/.env")


def create_stock_price_agent_graph():
    """
    ChatClovaX 기반 독립적인 Stock Price Agent StateGraph 생성
    
    구조:
    - stock_agent_node: ChatClovaX가 스스로 도구 선택 및 실행 판단
    - tools_node: Stock Price Agent 전용 도구들 실행
    - 조건부 라우팅: tools_condition으로 tool_calls 존재 여부 확인
    
    Returns:
        StateGraph: 컴파일된 Stock Price Agent StateGraph
    """
    
    # ChatClovaX 초기화 (HCX-005 모델)
    stock_llm = ChatClovaX(
        model=os.getenv('CLOVA_MODEL', 'HCX-005'),
        temperature=float(os.getenv('CLOVA_TEMPERATURE', '0')),
        naver_clovastudio_api_key=os.getenv('NAVER_CLOVASTUDIO_API_KEY'),
        naver_clovastudio_apigw_api_key=os.getenv('NAVER_CLOVASTUDIO_APIGW_API_KEY')
    )
    
    print("✅ Direct Stock Price Agent: ChatClovaX (HCX-005) 사용")
    
    # Stock Price Agent 전용 도구들
    stock_tools = get_direct_stock_price_tools()
    
    # ChatClovaX에 도구들 바인딩
    llm_with_tools = stock_llm.bind_tools(stock_tools)
    
    # 데이터 매니저 초기화
    data_manager = get_data_manager()
    
    def stock_agent_node(state: MessagesState) -> MessagesState:
        """
        Stock Agent 노드: ChatClovaX가 스스로 도구 선택 및 실행 판단
        
        Args:
            state: 현재 메시지 상태
            
        Returns:
            MessagesState: 업데이트된 상태
        """
        messages = state["messages"]
        
        # 프롬프트 포맷팅을 위한 도구 정보 수집
        tools_info = _get_tools_info(stock_tools)
        formatted_prompt = DIRECT_STOCK_PRICE_AGENT_PROMPT.format(**tools_info)
        
        # 시스템 메시지와 함께 ChatClovaX 호출
        prompt_messages = [HumanMessage(content=formatted_prompt)] + messages
        response = llm_with_tools.invoke(prompt_messages)
        
        # 메타데이터 업데이트
        updated_metadata = state.get("metadata", {})
        updated_metadata.update({
            "stock_agent_processed": True,
            "model_used": "ChatClovaX_HCX-005",
            "tools_available": len(stock_tools)
        })
        
        return {
            "messages": messages + [response],
            "metadata": updated_metadata
        }
    
    # ToolNode로 Stock Price Agent 전용 도구들 실행
    tools_node = ToolNode(stock_tools)
    
    def enhanced_tools_node(state: MessagesState) -> MessagesState:
        """
        개선된 Tools 노드: 실행 후 추가 정보 포함
        
        Args:
            state: 현재 상태
            
        Returns:
            MessagesState: 도구 실행 결과가 포함된 상태
        """
        # 기본 ToolNode 실행
        result_state = tools_node.invoke(state)
        
        # 데이터 처리 요약 정보 추가
        data_summary = data_manager.get_data_summary()
        if data_summary['filtered_files'] > 0:
            summary_text = f"\n\n📊 데이터 처리 요약:\n• 저장된 파일: {data_summary['filtered_files']}개\n• 총 크기: {data_summary['total_size_mb']}MB"
            
            # 마지막 ToolMessage에 요약 추가
            if result_state["messages"] and hasattr(result_state["messages"][-1], 'content'):
                result_state["messages"][-1].content += summary_text
        
        # 메타데이터 업데이트
        updated_metadata = result_state.get("metadata", {})
        updated_metadata.update({
            "data_files_created": data_summary['filtered_files'],
            "total_data_size_mb": data_summary['total_size_mb']
        })
        
        result_state["metadata"] = updated_metadata
        return result_state
    
    # StateGraph 구성
    workflow = StateGraph(MessagesState)
    
    # 노드 추가
    workflow.add_node("stock_agent", stock_agent_node)
    workflow.add_node("tools", enhanced_tools_node)
    
    # 엣지 정의
    workflow.add_edge(START, "stock_agent")
    
    # 조건부 엣지: tool_calls 존재 여부에 따라 분기
    workflow.add_conditional_edges(
        "stock_agent",
        tools_condition,  # ChatClovaX의 tool_calls 감지
        {
            "tools": "tools",      # tool_calls 있으면 tools 노드로
            "__end__": END         # tool_calls 없으면 종료 (표 데이터와 함께)
        }
    )
    
    # tools 실행 후 다시 stock_agent로 복귀
    workflow.add_edge("tools", "stock_agent")
    
    # 그래프 컴파일
    compiled_graph = workflow.compile()
    
    print("✅ Direct Stock Price Agent Graph 컴파일 완료")
    return compiled_graph


def _get_tools_info(tools: List) -> Dict[str, str]:
    """
    도구 정보를 프롬프트에 사용할 수 있는 형태로 변환
    
    Args:
        tools: 도구 리스트
        
    Returns:
        Dict: 프롬프트 포맷팅용 도구 정보
    """
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


class DirectStockPriceAgent:
    """
    ChatClovaX 기반 Direct Stock Price Agent (Wrapper 클래스)
    하위 호환성을 위한 래퍼
    """
    
    def __init__(self, llm: ChatClovaX = None):
        """
        Direct Stock Price Agent 초기화
        
        Args:
            llm: ChatClovaX 인스턴스 (사용되지 않음, 하위 호환성용)
        """
        self.graph = create_stock_price_agent_graph()
        self.data_manager = get_data_manager()
        
        print("🤖 Direct Stock Price Agent 초기화: ChatClovaX (HCX-005)")
        print("📁 독립적 StateGraph 구조로 초기화 완료")
    
    def invoke(self, state: MessagesState) -> Dict[str, Any]:
        """
        Stock Price Agent를 실행합니다 (Direct StateGraph 방식)
        
        Args:
            state: 현재 상태
            
        Returns:
            Dict: 업데이트된 상태
        """
        try:
            # Direct StateGraph 실행
            result = self.graph.invoke(state)
            return result
            
        except Exception as e:
            # 오류 처리
            error_message = f"Direct Stock Price Agent 처리 중 오류 발생: {str(e)}"
            
            error_ai_message = AIMessage(content=error_message)
            
            updated_state = state.copy()
            updated_state["messages"] = state["messages"] + [error_ai_message]
            updated_state["error"] = str(e)
            
            return updated_state 