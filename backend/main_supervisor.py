#!/usr/bin/env python3
"""
ChatClovaX 기반 Supervisor 멀티 에이전트 시스템
메인 서버 스크립트 (langgraph-supervisor 패턴)

이 스크립트는 주식 분석을 위한 멀티 에이전트 시스템을 실행합니다:
- Supervisor Agent: ChatClovaX 기반 사용자 질문 분석 및 워커 에이전트 조정
- Stock Price Agent: ChatClovaX 기반 키움증권 API를 통한 주식 데이터 조회

Architecture: LangGraph Supervisor MAS (ChatClovaX)
Environment: Local Development + Production Ready
LLM: ChatClovaX HCX-005 for all agents

uvicorn agents.supervisor.api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경변수 로드
load_dotenv("secrets/.env")

def print_system_info():
    """시스템 정보 출력 (ChatClovaX 기반)"""
    print("=" * 70)
    print("🤖 ChatClovaX Supervisor MAS for Stock Analysis")
    print("🚀 NAVER CLOVA X POWERED SYSTEM")
    print("=" * 70)
    print(f"📊 Architecture: LangGraph Supervisor Multi-Agent System")
    print(f"🔧 Framework: LangGraph + langgraph-supervisor")
    print(f"🧠 LLM Model: ChatClovaX HCX-005 (모든 Agent)")
    print(f"📈 Data Source: Kiwoom Securities REST API")
    print(f"💻 Environment: Local Development + Production Ready")
    
    # API 키 상태 확인
    clova_api = "✅ 설정됨" if os.getenv('CLOVASTUDIO_API_KEY') else "❌ 없음"
    langsmith_api = "✅ 설정됨" if os.getenv('LANGSMITH_API_KEY') else "❌ 없음"
    
    print(f"\n🔑 API Key Status:")
    print(f"  • CLOVASTUDIO_API_KEY: {clova_api}")
    print(f"  • LANGSMITH_API_KEY: {langsmith_api}")
    
    # LangSmith 정보
    if os.getenv('LANGSMITH_API_KEY'):
        project = os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis')
        print(f"\n📊 LangSmith: Enabled")
        print(f"  • Project: {project}")
        print(f"  • Dashboard: https://smith.langchain.com/")
    else:
        print(f"\n📊 LangSmith: Disabled")
    
    print("\n🔧 Agent Configuration (ChatClovaX HCX-005):")
    print(f"  • Supervisor Agent: 질문 분석 및 워커 에이전트 조정")
    print(f"  • Stock Price Agent: 키움증권 API 데이터 수집 및 분석")
    
    print("\n🏗️  System Features:")
    print(f"  • langgraph-supervisor 패턴")
    print(f"  • Manual fallback 지원")
    print(f"  • ChatClovaX 통합 Tool Calling")
    print(f"  • 실시간 주가 데이터 분석")
    print(f"  • FastAPI REST API 서버")

def check_environment():
    """환경 설정 확인"""
    print("\n🔍 환경 설정 검증:")
    
    # 필수 API 키 확인
    clova_key = os.getenv('CLOVASTUDIO_API_KEY')
    if not clova_key:
        print("  ❌ CLOVASTUDIO_API_KEY가 설정되지 않았습니다.")
        print("     secrets/.env 파일에 API 키를 추가해주세요.")
        return False
    else:
        print("  ✅ CLOVASTUDIO_API_KEY 확인됨")
    
    # 패키지 import 테스트
    try:
        from langchain_naver import ChatClovaX
        print("  ✅ langchain_naver 패키지 설치됨")
    except ImportError:
        print("  ❌ langchain_naver 패키지가 설치되지 않았습니다.")
        print("     'pip install langchain-naver'를 실행해주세요.")
        return False
    
    try:
        from agents.shared.graph import create_supervisor_graph
        print("  ✅ Supervisor 그래프 모듈 확인됨")
    except ImportError as e:
        print(f"  ❌ Supervisor 그래프 모듈 import 실패: {e}")
        return False
    
    print("  ✅ 환경 설정이 올바릅니다.")
    return True

def run_api_server(host: str = None, port: int = None, reload: bool = None):
    """API 서버 실행"""
    print("\n🚀 ChatClovaX Supervisor API 서버 시작...")
    
    # 환경 설정 확인
    if not check_environment():
        print("\n❌ 환경 설정 문제로 인해 서버를 시작할 수 없습니다.")
        return
    
    # 서버 설정
    if host is None:
        host = os.getenv('SERVER_HOST', '0.0.0.0')
    if port is None:
        port = int(os.getenv('SERVER_PORT', '8000'))
    if reload is None:
        reload = os.getenv('SERVER_RELOAD', 'true').lower() == 'true'
    
    print(f"\n🌐 서버 정보:")
    print(f"  • 주소: http://{host}:{port}")
    print(f"  • 핫 리로드: {'활성화' if reload else '비활성화'}")
    print(f"  • API 문서: http://{host}:{port}/docs")
    print(f"  • 헬스체크: http://{host}:{port}/health")
    
    try:
        import uvicorn
        from agents.supervisor.api import app
        
        print(f"\n⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔥 서버가 시작됩니다...")
        
        # 환경변수 설정
        os.environ["REQUEST_TIME"] = datetime.now().isoformat()
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 서버가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 중 오류 발생: {e}")

def run_interactive_mode():
    """대화형 모드 실행"""
    print("\n💬 ChatClovaX Supervisor 대화형 모드 시작...")
    
    # 환경 설정 확인
    if not check_environment():
        print("\n❌ 환경 설정 문제로 인해 대화형 모드를 시작할 수 없습니다.")
        return
    
    try:
        from agents.shared.graph import create_supervisor_graph, create_initial_state, extract_final_answer
        
        # 그래프 생성
        print("🤖 Supervisor 시스템 초기화 중...")
        graph = create_supervisor_graph()
        print("✅ 시스템이 준비되었습니다!\n")
        
        print("=" * 50)
        print("💬 ChatClovaX 주식 분석 시스템에 오신 것을 환영합니다!")
        print("📝 주식 관련 질문을 입력하세요 (종료: 'quit' 또는 'exit')")
        print("=" * 50)
        
        while True:
            try:
                # 사용자 입력
                user_input = input("\n👤 질문: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 대화형 모드를 종료합니다.")
                    break
                
                if not user_input:
                    print("❓ 질문을 입력해주세요.")
                    continue
                
                # 처리 시작
                print(f"🤖 ChatClovaX Supervisor 처리 중...")
                start_time = datetime.now()
                
                # 그래프 실행
                initial_state = create_initial_state(user_input)
                final_state = graph.invoke(initial_state)
                
                # 결과 추출
                answer = extract_final_answer(final_state)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # 결과 출력
                print(f"\n🤖 ChatClovaX 응답 ({processing_time:.2f}초):")
                print("=" * 50)
                print(answer)
                print("=" * 50)
                
            except KeyboardInterrupt:
                print("\n\n🛑 사용자에 의해 중단되었습니다.")
                break
            except Exception as e:
                print(f"\n❌ 처리 중 오류 발생: {e}")
                
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")

def run_test_mode():
    """테스트 모드 실행"""
    print("\n🧪 ChatClovaX Supervisor 테스트 모드 시작...")
    
    try:
        # 테스트 스크립트 실행
        from test_new_supervisor import main as test_main
        test_main()
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="ChatClovaX 기반 Supervisor 멀티 에이전트 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main_supervisor.py                   # API 서버 모드 (기본)
  python main_supervisor.py --mode interactive  # 대화형 모드
  python main_supervisor.py --mode test        # 테스트 모드
  python main_supervisor.py --host 127.0.0.1 --port 8080  # 사용자 정의 서버 설정
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['server', 'interactive', 'test'],
        default='server',
        help='실행 모드 선택 (기본: server)'
    )
    parser.add_argument(
        '--host',
        default=None,
        help='서버 호스트 (기본: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='서버 포트 (기본: 8000)'
    )
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='핫 리로드 비활성화'
    )
    
    args = parser.parse_args()
    
    # 시스템 정보 출력
    print_system_info()
    
    # 모드별 실행
    if args.mode == 'server':
        reload = not args.no_reload
        run_api_server(args.host, args.port, reload)
    elif args.mode == 'interactive':
        run_interactive_mode()
    elif args.mode == 'test':
        run_test_mode()

if __name__ == "__main__":
    main() 