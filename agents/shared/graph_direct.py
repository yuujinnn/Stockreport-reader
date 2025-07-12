"""
ChatClovaX 기반 Direct StateGraph 구현
Handoff Tool 패턴 적용한 멀티 에이전트 시스템
"""

import os
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_naver import ChatClovaX
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from dotenv import load_dotenv

from .state import MessagesState
from ..supervisor.agent_direct import DirectSupervisorAgent
from ..stock_price_agent.agent_direct import create_stock_price_agent_graph

# 환경변수 로드
load_dotenv("secrets/.env")


def create_handoff_tool(agent_name: str, description: str, agent_graph):
    """
    Handoff Tool 생성 팩토리
    
    Args:
        agent_name: 에이전트 이름
        description: 에이전트 설명
        agent_graph: 해당 에이전트의 StateGraph
        
    Returns:
        tool: Handoff 도구
    """
    @tool(f"handoff_to_{agent_name}")
    def handoff_tool(request: str) -> str:
        f"""{description}를 위해 {agent_name}에게 작업을 위임합니다.
        
        Args:
            request: {agent_name}에게 전달할 평문 요청. 종목명, 티커, 기간, 분석 목적을 구체적으로 포함해야 함.
            
        Returns:
            str: {agent_name}의 처리 결과 (표 형태 데이터 포함)
        """
        try:
            # Sub-agent StateGraph 실행
            initial_state = {
                "messages": [HumanMessage(content=request)],
                "user_query": request,
                "extracted_info": None,
                "stock_data": None,
                "error": None,
                "metadata": {"source": f"handoff_from_supervisor", "target_agent": agent_name}
            }
            
            # 해당 에이전트 그래프 실행
            result_state = agent_graph.invoke(initial_state)
            
            # 최종 결과 추출
            result_messages = result_state.get("messages", [])
            if result_messages:
                # 마지막 AI 메시지의 content 반환
                for message in reversed(result_messages):
                    if isinstance(message, AIMessage):
                        return message.content
            
            return f"{agent_name} 처리 완료되었으나 결과를 찾을 수 없습니다."
            
        except Exception as e:
            return f"{agent_name} 처리 중 오류 발생: {str(e)}"
    
    return handoff_tool


def create_direct_supervisor_graph():
    """
    ChatClovaX 기반 Direct StateGraph Supervisor 생성
    
    구조:
    - supervisor_node: ChatClovaX로 handoff tools 사용 판단
    - tools_node: handoff tools 실행하여 sub-agent 호출
    - 조건부 라우팅: tools_condition으로 tool_calls 존재 여부 확인
    
    Returns:
        StateGraph: 컴파일된 Direct StateGraph
    """
    
    # ChatClovaX 초기화 (HCX-005 모델)
    supervisor_llm = ChatClovaX(
        model=os.getenv('CLOVA_MODEL', 'HCX-005'),
        temperature=float(os.getenv('CLOVA_TEMPERATURE', '0')),
        naver_clovastudio_api_key=os.getenv('NAVER_CLOVASTUDIO_API_KEY'),
        naver_clovastudio_apigw_api_key=os.getenv('NAVER_CLOVASTUDIO_APIGW_API_KEY')
    )
    
    print("✅ Direct Supervisor: ChatClovaX (HCX-005) 사용")
    
    # Sub-agent StateGraphs 생성
    stock_price_agent_graph = create_stock_price_agent_graph()
    print("✅ Stock Price Agent: 독립적 StateGraph 생성")
    
    # Handoff Tools 생성
    handoff_tools = [
        create_handoff_tool(
            agent_name="stock_agent",
            description="주식 데이터 분석, 차트 조회, 종목 분석",
            agent_graph=stock_price_agent_graph
        ),
        # 향후 추가될 다른 에이전트들
        # create_handoff_tool("market_agent", "시장 전반 분석", market_agent_graph),
        # create_handoff_tool("news_agent", "뉴스 분석", news_agent_graph),
    ]
    
    # ChatClovaX에 handoff tools 바인딩
    llm_with_tools = supervisor_llm.bind_tools(handoff_tools)
    
    def supervisor_node(state: MessagesState) -> MessagesState:
        """
        Supervisor 노드: ChatClovaX가 스스로 handoff 판단
        
        Args:
            state: 현재 메시지 상태
            
        Returns:
            MessagesState: 업데이트된 상태
        """
        messages = state["messages"]
        
        # ChatClovaX로 handoff 판단 및 실행
        response = llm_with_tools.invoke(messages)
        
        # 메타데이터 업데이트
        updated_metadata = state.get("metadata", {})
        updated_metadata.update({
            "supervisor_processed": True,
            "model_used": "ChatClovaX_HCX-005",
            "pattern": "direct_handoff_supervisor"
        })
        
        return {
            "messages": messages + [response],
            "metadata": updated_metadata
        }
    
    # ToolNode로 handoff tools 실행
    tools_node = ToolNode(handoff_tools)
    
    # StateGraph 구성
    workflow = StateGraph(MessagesState)
    
    # 노드 추가
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("tools", tools_node)
    
    # 엣지 정의
    workflow.add_edge(START, "supervisor")
    
    # 조건부 엣지: tool_calls 존재 여부에 따라 분기
    workflow.add_conditional_edges(
        "supervisor",
        tools_condition,  # ChatClovaX의 tool_calls 감지
        {
            "tools": "tools",      # tool_calls 있으면 tools 노드로
            "__end__": END         # tool_calls 없으면 종료
        }
    )
    
    # tools 실행 후 다시 supervisor로 복귀
    workflow.add_edge("tools", "supervisor")
    
    # 그래프 컴파일
    compiled_graph = workflow.compile()
    
    print("✅ Direct Supervisor Graph 컴파일 완료")
    return compiled_graph


def create_initial_state(user_query: str) -> MessagesState:
    """
    Direct StateGraph용 초기 상태 생성
    
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
            "pattern": "direct_handoff_supervisor", 
            "architecture": "chatclovax_direct",
            "model": "HCX-005"
        }
    )


def extract_final_answer(state: MessagesState) -> str:
    """
    Direct StateGraph 최종 상태에서 답변 추출
    
    Args:
        state: 최종 상태
        
    Returns:
        str: 최종 답변
    """
    messages = state["messages"]
    
    # 마지막 AI 메시지 찾기
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = getattr(message, 'content', '')
            if isinstance(content, str) and content.strip():
                return content.strip()
    
    # 오류 상태 확인
    if state.get("error"):
        return f"처리 중 오류가 발생했습니다: {state['error']}"
    
    return "죄송합니다. 적절한 답변을 생성할 수 없었습니다." 