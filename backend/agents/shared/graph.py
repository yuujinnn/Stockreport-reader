"""
LangGraph 기반 Supervisor MAS 그래프 정의
ChatClovaX + langgraph-supervisor 패턴 구현
"""

import os
from langgraph.graph import StateGraph, START, END
from langchain_naver import ChatClovaX
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from .state import MessagesState
from ..supervisor.agent import SupervisorAgent

# 환경변수 로드
load_dotenv("../../secrets/.env")


def create_supervisor_graph():
    """
    ChatClovaX 기반 Supervisor MAS 그래프를 생성합니다.
    
    새로운 구조:
    - Supervisor: ChatClovaX (HCX-005) 기반 총괄 감독관
    - Stock Price Agent: ChatClovaX (HCX-005) 기반 주가 분석 전문가
    - langgraph-supervisor 또는 수동 구현으로 협업
    
    Returns:
        StateGraph: 컴파일된 LangGraph
    """
    
    try:
        # CLOVA Studio API 키 확인
        clova_api_key = os.getenv('CLOVASTUDIO_API_KEY')
        if not clova_api_key:
            raise ValueError("CLOVASTUDIO_API_KEY가 설정되지 않았습니다.")
        
        print("🤖 ChatClovaX 기반 Supervisor 시스템 초기화 중...")
        print(f"🔑 CLOVA Studio API 키: {'설정됨' if clova_api_key else '없음'}")
        
        # Supervisor Agent 생성 (ChatClovaX 기반)
        supervisor_agent = SupervisorAgent()
        
        # Simple StateGraph 생성 (Supervisor 중심 구조)
        workflow = StateGraph(MessagesState)
        
        # Supervisor 노드 추가
        workflow.add_node("supervisor", supervisor_agent.invoke)
        
        # 간단한 플로우: START -> supervisor -> END
        workflow.add_edge(START, "supervisor")
        workflow.add_edge("supervisor", END)
        
        # 그래프 컴파일
        graph = workflow.compile()
        
        print("✅ ChatClovaX 기반 Supervisor 그래프 생성 완료")
        print("🏗️  구조: START -> Supervisor (ChatClovaX) -> END")
        print("👥 협업 방식: Supervisor가 Stock Price Agent 조정")
        
        return graph
        
    except Exception as e:
        print(f"❌ 그래프 생성 실패: {e}")
        raise


def create_initial_state(user_query: str, context: str = "") -> MessagesState:
    """
    초기 상태를 생성합니다.
    
    Args:
        user_query: 사용자 질문
        context: 인용된 문서 컨텍스트 (선택사항)
        
    Returns:
        MessagesState: 초기 상태
    """
    initial_message = HumanMessage(content=user_query)
    
    metadata = {
        "system": "ChatClovaX_Supervisor",
        "model": "HCX-005",
        "pattern": "langgraph_supervisor",
        "created_at": os.getenv("REQUEST_TIME", "unknown")
    }
    
    # 컨텍스트 정보가 있으면 메타데이터에 추가
    if context and context.strip():
        metadata["has_context"] = True
        metadata["context_length"] = len(context)
    else:
        metadata["has_context"] = False
    
    return MessagesState(
        messages=[initial_message],
        user_query=user_query,
        context=context,
        extracted_info=None,
        stock_data=None,
        error=None,
        metadata=metadata
    )


def extract_final_answer(final_state: MessagesState) -> str:
    """
    최종 상태에서 답변을 추출합니다.
    
    Args:
        final_state: 최종 상태
        
    Returns:
        str: 최종 답변
    """
    try:
        messages = final_state.get("messages", [])
        
        if not messages:
            return "응답을 생성할 수 없습니다."
        
        # 마지막 AI 메시지 찾기
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content
        
        # AI 메시지가 없다면 마지막 메시지 반환
        last_message = messages[-1]
        if hasattr(last_message, 'content') and last_message.content:
            return last_message.content
        
        return "응답을 처리할 수 없습니다."
        
    except Exception as e:
        return f"답변 추출 중 오류 발생: {str(e)}"


def get_graph_status() -> dict:
    """
    그래프 시스템 상태를 반환합니다.
    
    Returns:
        dict: 시스템 상태 정보
    """
    return {
        "system": "ChatClovaX Supervisor MAS",
        "supervisor_model": "HCX-005 (ChatClovaX)",
        "worker_agents": ["Stock Price Agent (HCX-005)"],
        "pattern": "langgraph-supervisor + manual fallback",
        "api_dependencies": ["CLOVASTUDIO_API_KEY"],
        "framework": "LangGraph + LangChain + ChatClovaX",
        "status": "active" if os.getenv('CLOVASTUDIO_API_KEY') else "api_key_missing"
    } 