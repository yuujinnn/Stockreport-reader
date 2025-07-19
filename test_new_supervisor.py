"""
ChatClovaX 기반 새로운 Supervisor 시스템 테스트
"""

import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv("secrets/.env")

def test_environment():
    """환경변수 확인"""
    print("🔍 환경변수 확인:")
    print(f"  CLOVASTUDIO_API_KEY: {'✅ 설정됨' if os.getenv('CLOVASTUDIO_API_KEY') else '❌ 없음'}")
    print(f"  LANGSMITH_API_KEY: {'✅ 설정됨' if os.getenv('LANGSMITH_API_KEY') else '❌ 없음'}")
    
def test_imports():
    """패키지 import 테스트"""
    print("\n📦 패키지 import 테스트:")
    
    try:
        from langchain_naver import ChatClovaX
        print("  ✅ langchain_naver.ChatClovaX")
    except ImportError as e:
        print(f"  ❌ langchain_naver.ChatClovaX: {e}")
        return False
    
    try:
        from langgraph_supervisor import create_supervisor
        print("  ✅ langgraph_supervisor.create_supervisor")
    except ImportError as e:
        print(f"  ❌ langgraph_supervisor.create_supervisor: {e}")
        print("  ⚠️  langgraph-supervisor 대신 수동 구현을 사용합니다")
    
    try:
        from agents.supervisor.agent import SupervisorAgent
        print("  ✅ agents.supervisor.agent.SupervisorAgent")
    except ImportError as e:
        print(f"  ❌ agents.supervisor.agent.SupervisorAgent: {e}")
        return False
    
    return True

def test_supervisor_creation():
    """Supervisor Agent 생성 테스트"""
    print("\n🤖 Supervisor Agent 생성 테스트:")
    
    if not os.getenv('CLOVASTUDIO_API_KEY'):
        print("  ❌ CLOVASTUDIO_API_KEY가 설정되지 않아 테스트를 건너뜁니다")
        return False
    
    try:
        from agents.supervisor.agent import SupervisorAgent
        supervisor = SupervisorAgent()
        print("  ✅ SupervisorAgent 생성 성공")
        return True
    except Exception as e:
        print(f"  ❌ SupervisorAgent 생성 실패: {e}")
        return False

def test_graph_creation():
    """그래프 생성 테스트"""
    print("\n🏗️  그래프 생성 테스트:")
    
    if not os.getenv('CLOVASTUDIO_API_KEY'):
        print("  ❌ CLOVASTUDIO_API_KEY가 설정되지 않아 테스트를 건너뜁니다")
        return False
    
    try:
        from agents.shared.graph import create_supervisor_graph
        graph = create_supervisor_graph()
        print("  ✅ Supervisor 그래프 생성 성공")
        return True
    except Exception as e:
        print(f"  ❌ Supervisor 그래프 생성 실패: {e}")
        return False

def test_simple_query():
    """간단한 질의 테스트"""
    print("\n💬 간단한 질의 테스트:")
    
    if not os.getenv('CLOVASTUDIO_API_KEY'):
        print("  ❌ CLOVASTUDIO_API_KEY가 설정되지 않아 테스트를 건너뜁니다")
        return False
    
    try:
        from agents.shared.graph import create_supervisor_graph, create_initial_state, extract_final_answer
        
        # 그래프 생성
        graph = create_supervisor_graph()
        
        # 테스트 질문
        test_query = "안녕하세요. 시스템이 정상적으로 작동하는지 확인해주세요."
        
        # 초기 상태 생성
        initial_state = create_initial_state(test_query)
        
        # 그래프 실행
        print(f"  📝 테스트 질문: {test_query}")
        print("  🤖 처리 중...")
        
        final_state = graph.invoke(initial_state)
        
        # 결과 추출
        answer = extract_final_answer(final_state)
        
        print(f"  💬 응답: {answer[:100]}...")
        print("  ✅ 간단한 질의 테스트 성공")
        return True
        
    except Exception as e:
        print(f"  ❌ 간단한 질의 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 ChatClovaX 기반 Supervisor 시스템 테스트 시작\n")
    
    # 환경변수 확인
    test_environment()
    
    # 패키지 import 테스트
    if not test_imports():
        print("\n❌ 필수 패키지 import에 실패했습니다. 테스트를 종료합니다.")
        return
    
    # Supervisor 생성 테스트
    if not test_supervisor_creation():
        print("\n❌ Supervisor 생성에 실패했습니다.")
        return
    
    # 그래프 생성 테스트
    if not test_graph_creation():
        print("\n❌ 그래프 생성에 실패했습니다.")
        return
    
    # 간단한 질의 테스트
    test_simple_query()
    
    print("\n🎉 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main() 