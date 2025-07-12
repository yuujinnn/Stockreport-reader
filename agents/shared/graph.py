"""
LangGraph 기반 Supervisor MAS 그래프 정의
표준 Tool-calling Supervisor 패턴 구현 (OpenAI 전용)
"""

import os
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from .state import MessagesState
from ..supervisor.agent import SupervisorAgent

# 환경변수 로드
load_dotenv("secrets/.env")


def create_supervisor_graph():
    """
    LangGraph 공식 Tool-calling Supervisor MAS 그래프를 생성합니다.
    
    공식 가이드의 Tool-calling Supervisor 패턴:
    - Supervisor가 Stock Price Agent를 표준 tool로 호출
    - 단일 노드 구조로 간단하고 효율적
    - LangGraph의 자동 tool call 처리 활용
    - 모든 Agent에서 OpenAI 사용
    
    Returns:
        StateGraph: 컴파일된 LangGraph
    """
    
    # Supervisor용 LLM 초기화 (OpenAI)
    supervisor_llm = ChatOpenAI(
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        temperature=float(os.getenv('OPENAI_TEMPERATURE', '0')),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Stock Price Agent용 LLM 초기화 (OpenAI 전용)
    stock_llm = ChatOpenAI(
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        temperature=float(os.getenv('OPENAI_TEMPERATURE', '0')),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    print("✅ Supervisor Agent: OpenAI (gpt-4o-mini) 사용")
    print("✅ Stock Price Agent: OpenAI (gpt-4o-mini) 사용")
    
    # Supervisor Agent 인스턴스 생성 (두 LLM 모두 OpenAI)
    supervisor_agent = SupervisorAgent(
        supervisor_llm=supervisor_llm,
        stock_llm=stock_llm
    )
    
    # StateGraph 생성 (표준 Tool-calling Supervisor 패턴)
    workflow = StateGraph(MessagesState)
    
    # Supervisor 노드만 추가 (모든 작업을 표준 tool로 처리)
    workflow.add_node("supervisor", supervisor_agent.invoke)
    
    # 단순한 엣지: START -> supervisor -> END (표준 패턴)
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", END)
    
    # 그래프 컴파일
    return workflow.compile()


def create_initial_state(user_query: str) -> MessagesState:
    """
    초기 상태를 생성합니다.
    
    Args:
        user_query: 사용자 질문
        
    Returns:
        MessagesState: 초기 상태
    """
    return MessagesState(
        messages=[HumanMessage(content=user_query)],
        user_query=user_query,
        extracted_info=None,
        stock_data=None,
        error=None,
        metadata={
            "created_at": os.environ.get("REQUEST_TIME", ""), 
            "pattern": "tool_calling_supervisor",
            "architecture": "langgraph_official"
        }
    )


def extract_final_answer(state: MessagesState) -> str:
    """
    최종 상태에서 답변을 추출합니다.
    
    Args:
        state: 최종 상태
        
    Returns:
        str: 최종 답변
    """
    messages = state["messages"]
    
    # 마지막 AI 메시지를 찾기 (표준 방식)
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = getattr(message, 'content', '')
            if isinstance(content, str) and content.strip():
                return content.strip()
    
    # AI 메시지가 없으면 오류 상태 확인
    if state.get("error"):
        return f"처리 중 오류가 발생했습니다: {state['error']}"
    
    return "죄송합니다. 적절한 답변을 생성할 수 없었습니다." 