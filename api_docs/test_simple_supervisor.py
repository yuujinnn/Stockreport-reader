"""
ChatClovaX 기반 간단한 Supervisor 테스트
Math Agent + Research Agent 조합
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv("secrets/.env")

def test_simple_math_tools():
    """기본 수학 도구들 정의"""
    
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(a: float, b: float) -> float:
        """Divide two numbers."""
        return a / b

    return [add, multiply, divide]

def create_simple_agents():
    """간단한 math agent와 research agent 생성"""
    from langchain_naver import ChatClovaX
    from langchain_tavily import TavilySearch
    from langgraph.prebuilt import create_react_agent
    
    # ChatClovaX 모델 초기화
    llm = ChatClovaX(
        model="HCX-005",
        max_tokens=4096,
        temperature=0.1,
    )
    
    # Research Agent (Tavily 검색 도구)
    web_search = TavilySearch(max_results=3)
    
    research_agent = create_react_agent(
        llm,
        tools=[web_search],
        prompt=(
            "You are a research agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with research-related tasks, DO NOT do any math\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
    )
    
    # Math Agent (기본 수학 함수들)
    math_tools = test_simple_math_tools()
    
    math_agent = create_react_agent(
        llm,
        tools=math_tools,
        prompt=(
            "You are a math agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with math-related tasks\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
    )
    
    return research_agent, math_agent

def test_langgraph_supervisor():
    """langgraph-supervisor 패턴 테스트"""
    print("🧪 ChatClovaX + langgraph-supervisor 테스트 시작\n")
    
    # 환경변수 확인
    clova_key = os.getenv('CLOVASTUDIO_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    print("🔍 환경변수 확인:")
    print(f"  CLOVASTUDIO_API_KEY: {'✅ 설정됨' if clova_key else '❌ 없음'}")
    print(f"  TAVILY_API_KEY: {'✅ 설정됨' if tavily_key else '❌ 없음'}")
    
    # TAVILY_API_KEY가 없으면 임시로 설정
    if not tavily_key:
        print("  ⚠️  TAVILY_API_KEY가 없어서 임시로 설정합니다...")
        os.environ["TAVILY_API_KEY"] = "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"  # 사용자 제공 키
        tavily_key = os.getenv('TAVILY_API_KEY')
        print(f"  TAVILY_API_KEY (임시): {'✅ 설정됨' if tavily_key else '❌ 실패'}")
    
    if not clova_key:
        print("\n❌ CLOVASTUDIO_API_KEY가 누락되었습니다.")
        return False
    
    try:
        from langchain_naver import ChatClovaX
        from langgraph_supervisor import create_supervisor
        
        print("\n🤖 Agent 생성 중...")
        research_agent, math_agent = create_simple_agents()
        print("  ✅ Research Agent 생성 완료")
        print("  ✅ Math Agent 생성 완료")
        
        # ChatClovaX Supervisor 모델
        supervisor_llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,
            temperature=0.1,
        )
        
        print("\n🏗️  Supervisor 생성 중...")
        supervisor = create_supervisor(
            model=supervisor_llm,
            agents=[research_agent, math_agent],
            prompt=(
                "You are a supervisor managing two agents:\n"
                "- a research agent. Assign research-related tasks to this agent\n"
                "- a math agent. Assign math-related tasks to this agent\n"
                "Assign work to one agent at a time, do not call agents in parallel.\n"
                "Do not do any work yourself."
            ),
            add_handoff_back_messages=True,
            output_mode="full_history",
        ).compile()
        print("  ✅ Supervisor 생성 완료")
        
        print("\n💬 테스트 질의 실행...")
        test_query = "what is 3 + 5 multiplied by 7?"
        print(f"  📝 질문: {test_query}")
        
        result = supervisor.invoke({
            "messages": [{"role": "user", "content": test_query}]
        })
        
        # 결과 추출
        messages = result.get("messages", [])
        if messages:
            final_answer = messages[-1].content
            print(f"  💬 응답: {final_answer}")
        else:
            print("  ❌ 응답을 받지 못했습니다.")
        
        print("\n✅ langgraph-supervisor 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ langgraph-supervisor 테스트 실패: {e}")
        return False

def test_manual_supervisor():
    """수동 구현 Supervisor 패턴 테스트"""
    print("\n🔧 수동 Supervisor 구현 테스트...")
    
    try:
        from langchain_naver import ChatClovaX
        from langgraph.graph import StateGraph, START, END
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage, AIMessage
        from typing_extensions import TypedDict
        from typing import List
        
        # 간단한 상태 정의
        class SimpleState(TypedDict):
            messages: List
        
        # Agent 생성
        research_agent, math_agent = create_simple_agents()
        
        # Supervisor 모델
        supervisor_llm = ChatClovaX(
            model="HCX-005",
            max_tokens=4096,
            temperature=0.1,
        )
        
        # Handoff 도구들
        @tool("call_research_agent")
        def call_research_agent(request: str) -> str:
            """Call research agent for web search tasks"""
            try:
                result = research_agent.invoke({"messages": [HumanMessage(content=request)]})
                return result["messages"][-1].content
            except Exception as e:
                return f"Research agent error: {str(e)}"
        
        @tool("call_math_agent")
        def call_math_agent(request: str) -> str:
            """Call math agent for calculation tasks"""
            try:
                result = math_agent.invoke({"messages": [HumanMessage(content=request)]})
                return result["messages"][-1].content
            except Exception as e:
                return f"Math agent error: {str(e)}"
        
        # Supervisor agent
        from langgraph.prebuilt import create_react_agent
        
        supervisor_agent = create_react_agent(
            supervisor_llm,
            tools=[call_research_agent, call_math_agent],
            prompt=(
                "You are a supervisor managing two agents:\n"
                "- call_research_agent: for web search and research tasks\n"
                "- call_math_agent: for mathematical calculations\n"
                "Analyze the user's question and delegate to the appropriate agent.\n"
                "Do not do any work yourself."
            ),
        )
        
        # 간단한 그래프
        workflow = StateGraph(SimpleState)
        workflow.add_node("supervisor", supervisor_agent)
        workflow.add_edge(START, "supervisor")
        workflow.add_edge("supervisor", END)
        
        graph = workflow.compile()
        
        print("  ✅ 수동 Supervisor 생성 완료")
        
        # 테스트 실행
        test_query = "what is 3 + 5 multiplied by 7?"
        print(f"  📝 질문: {test_query}")
        
        result = graph.invoke({
            "messages": [HumanMessage(content=test_query)]
        })
        
        messages = result.get("messages", [])
        if messages:
            final_answer = messages[-1].content
            print(f"  💬 응답: {final_answer}")
        else:
            print("  ❌ 응답을 받지 못했습니다.")
        
        print("  ✅ 수동 Supervisor 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"  ❌ 수동 Supervisor 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 ChatClovaX Supervisor 간단 테스트 시작\n")
    print("=" * 60)
    
    # langgraph-supervisor 패턴 테스트
    supervisor_success = test_langgraph_supervisor()
    
    # 실패한 경우 수동 구현 테스트
    if not supervisor_success:
        manual_success = test_manual_supervisor()
        
        if manual_success:
            print("\n💡 langgraph-supervisor는 실패했지만 수동 구현은 성공했습니다.")
            print("   ChatClovaX와 langgraph-supervisor 간 호환성 문제일 수 있습니다.")
        else:
            print("\n❌ 모든 테스트가 실패했습니다.")
            return
    
    print("\n🎉 테스트 완료!")
    print("💡 이제 StockPriceAgent 통합을 시도할 수 있습니다.")

if __name__ == "__main__":
    main() 