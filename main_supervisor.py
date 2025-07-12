#!/usr/bin/env python3
"""
LangGraph 기반 Supervisor 멀티 에이전트 시스템
메인 서버 스크립트 (로컬 개발 환경 최적화, OpenAI 전용)

이 스크립트는 주식 분석을 위한 멀티 에이전트 시스템을 실행합니다:
- Supervisor Agent: 사용자 질문 분석 및 워커 에이전트 조정 (OpenAI)
- Stock Price Agent: 키움증권 API를 통한 주식 데이터 조회 (OpenAI)

Architecture: LangGraph Supervisor MAS
Environment: Local Development Optimized
LLM: OpenAI (gpt-4o-mini) for all agents
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경변수 로드
load_dotenv("secrets/.env")

def print_system_info():
    """시스템 정보 출력 (로컬 환경 강조, OpenAI 전용)"""
    print("=" * 60)
    print("🤖 LangGraph Supervisor MAS for Stock Analysis")
    print("🏠 LOCAL DEVELOPMENT ENVIRONMENT (OpenAI 전용)")
    print("=" * 60)
    print(f"📊 Architecture: Supervisor Multi-Agent System")
    print(f"🔧 Framework: LangGraph + LangChain")
    print(f"🧠 LLM Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')} (모든 Agent)")
    print(f"📈 Data Source: Kiwoom Securities REST API")
    print(f"💻 Environment: Local Development")
    
    # LangSmith 정보 (LANGSMITH_API_KEY 사용)
    if os.getenv('LANGSMITH_API_KEY'):
        project = os.getenv('LANGSMITH_PROJECT', 'MiraeAssetAI')
        print(f"📊 LangSmith: Enabled (Project: {project})")
        print(f"🔗 Dashboard: https://smith.langchain.com/")
    else:
        print(f"📊 LangSmith: Disabled (개발 환경에서는 선택적)")
    
    print("\n🔧 Agent Configuration (OpenAI 전용):")
    print(f"  • Supervisor Agent: Query analysis & coordination (OpenAI)")
    print(f"  • Stock Price Agent: Kiwoom API data collection (OpenAI)")
    print("\n🏠 Local Development Features:")
    print(f"  • Hot reload: 파일 변경 시 자동 재시작")
    print(f"  • Debug mode: 상세 로깅 및 오류 추적")
    print(f"  • Kiwoom test: API 연결 상태 확인")
    print("=" * 60)


def check_requirements():
    """필수 의존성 및 환경변수 확인 (로컬 환경 가이드 포함)"""
    print("🔍 로컬 개발 환경 요구사항 확인 중...")
    
    # 환경변수 확인
    required_env_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 누락된 환경변수: {', '.join(missing_vars)}")
        print("📝 로컬 개발 환경 설정 가이드:")
        print("   1. secrets/.env 파일에 다음 변수들을 설정해주세요:")
        for var in missing_vars:
            print(f"      {var}=your_value_here")
        print("   2. 키움 API 키 파일도 확인해주세요:")
        print("      secrets/57295187_appkey.txt")
        print("      secrets/57295187_secretkey.txt")
        print("   3. 자세한 설정 방법은 .cursor/rules/development.md를 참조하세요")
        return False
    
    # 필수 라이브러리 확인
    try:
        import langgraph
        import langchain
        import fastapi
        print("✅ 모든 의존성이 설치되었습니다.")
        return True
    except ImportError as e:
        print(f"❌ 누락된 라이브러리: {e}")
        print("💡 로컬 환경 설정 명령어:")
        print("   pip install -r requirements.txt")
        print("   # 개발용 도구도 설치하려면:")
        print("   pip install pytest black flake8 mypy")
        return False


def run_supervisor_server(args):
    """Supervisor API 서버 실행 (로컬 환경 최적화)"""
    from agents.supervisor.api import run_supervisor_server
    
    print("\n🚀 로컬 개발용 Supervisor API 서버를 시작합니다...")
    print(f"📡 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"🐛 Debug: {args.debug}")
    
    # 로컬 환경 안내
    if args.host in ['127.0.0.1', 'localhost']:
        print(f"🏠 로컬 전용 모드 - 외부 접근 차단됨")
    elif args.host == '0.0.0.0':
        print(f"🌐 네트워크 모드 - 같은 네트워크에서 접근 가능")
    
    print(f"📱 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🏥 Health Check: http://{args.host}:{args.port}/health")
    print("=" * 60)
    
    # 디버그 모드 설정
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("🐛 디버그 모드 활성화 - 상세 로그가 출력됩니다")
    
    try:
        run_supervisor_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\n👋 로컬 개발 서버가 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 오류: {e}")
        print("💡 문제 해결 방법:")
        print("   1. 포트가 이미 사용 중인지 확인: netstat -ano | findstr :8000")
        print("   2. 다른 포트로 시도: python main_supervisor.py --port 8080")
        print("   3. 환경변수 설정 확인: secrets/.env 파일")
        sys.exit(1)


def run_legacy_server(args):
    """기존 단일 에이전트 서버 실행 (호환성용)"""
    from stock_price.api import run_server
    
    print("\n🔧 Legacy 단일 에이전트 서버를 시작합니다...")
    print(f"📡 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print("📝 이 모드는 호환성 목적으로만 사용하세요.")
    print("=" * 60)
    
    try:
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\n👋 서버가 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 오류: {e}")
        sys.exit(1)


def test_graph():
    """LangGraph 연결 및 기본 동작 테스트"""
    print("🧪 LangGraph 연결 테스트 중...")
    
    try:
        from agents.shared.graph import create_supervisor_graph, create_initial_state, extract_final_answer
        
        # 그래프 생성 테스트
        print("  • Supervisor 그래프 생성 중...")
        graph = create_supervisor_graph()
        print("  ✅ 그래프 생성 완료")
        
        # 간단한 상태 테스트
        print("  • 상태 생성 테스트 중...")
        test_state = create_initial_state("테스트 질문입니다")
        print("  ✅ 상태 생성 완료")
        
        print("✅ LangGraph 테스트 완료 - 시스템이 정상 작동합니다.")
        return True
        
    except Exception as e:
        print(f"❌ LangGraph 테스트 실패: {e}")
        print("💡 문제 해결 방법:")
        print("   1. 환경변수 확인: OPENAI_API_KEY 설정 여부")
        print("   2. 의존성 재설치: pip install -r requirements.txt")
        print("   3. Python 경로 확인: 프로젝트 루트에서 실행")
        return False


def test_kiwoom_connection():
    """키움 API 연결 테스트 (로컬 개발용)"""
    print("🔗 키움 API 연결 테스트 중...")
    
    try:
        from agents.stock_price_agent.kiwoom_api import get_token_manager
        
        # 키 파일 존재 확인
        appkey_file = "secrets/57295187_appkey.txt"
        secretkey_file = "secrets/57295187_secretkey.txt"
        
        if not os.path.exists(appkey_file):
            print(f"❌ 키움 앱키 파일 없음: {appkey_file}")
            return False
        
        if not os.path.exists(secretkey_file):
            print(f"❌ 키움 시크릿키 파일 없음: {secretkey_file}")
            return False
        
        print("  • 키움 API 키 파일 확인 완료")
        
        # 토큰 매니저 생성 테스트
        print("  • 토큰 매니저 생성 중...")
        token_manager = get_token_manager()
        print("  ✅ 토큰 매니저 생성 완료")
        
        # 토큰 발급 테스트 (실제 API 호출)
        print("  • 접근 토큰 발급 테스트 중...")
        token = token_manager.get_access_token()
        
        if token:
            print("  ✅ 키움 API 연결 성공 - 토큰 발급 완료")
            print(f"  📄 토큰 (앞 10자리): {token[:10]}...")
            return True
        else:
            print("  ❌ 토큰 발급 실패")
            return False
            
    except Exception as e:
        print(f"❌ 키움 API 연결 테스트 실패: {e}")
        print("💡 문제 해결 방법:")
        print("   1. 키움 API 키 파일 확인:")
        print("      secrets/57295187_appkey.txt")
        print("      secrets/57295187_secretkey.txt")
        print("   2. 네트워크 연결 확인")
        print("   3. 키움 API 서비스 상태 확인")
        return False


def main():
    """메인 실행 함수 (로컬 개발 환경 최적화)"""
    parser = argparse.ArgumentParser(
        description="LangGraph 기반 Supervisor 멀티 에이전트 주식 분석 시스템 (로컬 개발용)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
로컬 개발 환경 사용법:
  python main_supervisor.py                    # 로컬 서버 실행 (127.0.0.1:8000)
  python main_supervisor.py --debug            # 디버그 모드로 실행
  python main_supervisor.py --test             # 시스템 테스트
  python main_supervisor.py --kiwoom-test      # 키움 API 연결 테스트
  python main_supervisor.py --port 8080        # 포트 8080으로 실행
  python main_supervisor.py --host 0.0.0.0     # 네트워크 접근 허용

개발 도구:
  python main_supervisor.py --legacy           # Legacy 단일 에이전트 실행
  python main_supervisor.py --no-reload        # 자동 재시작 비활성화

로컬 환경 설정 가이드는 .cursor/rules/development.md를 참조하세요.
        """
    )
    
    # 서버 모드 선택
    parser.add_argument(
        '--legacy', 
        action='store_true',
        help='기존 단일 에이전트 모드로 실행 (호환성용)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true', 
        help='시스템 테스트만 수행하고 종료'
    )
    
    parser.add_argument(
        '--kiwoom-test',
        action='store_true',
        help='키움 API 연결 테스트만 수행하고 종료'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드 활성화 (상세 로깅)'
    )
    
    # 서버 설정 (로컬 환경 기본값)
    parser.add_argument(
        '--host',
        default=os.getenv('SERVER_HOST', '127.0.0.1'),  # 로컬 전용으로 변경
        help='서버 호스트 주소 (기본값: 127.0.0.1, 네트워크 접근시 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('SERVER_PORT', '8000')),
        help='서버 포트 번호 (기본값: 8000)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        default=os.getenv('SERVER_RELOAD', 'true').lower() == 'true',
        help='개발 모드 (파일 변경시 자동 재시작, 기본값: true)'
    )
    
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='자동 재시작 비활성화'
    )
    
    args = parser.parse_args()
    
    # --no-reload 옵션 처리
    if args.no_reload:
        args.reload = False
    
    # 시스템 정보 출력
    print_system_info()
    
    # 요구사항 확인
    if not check_requirements():
        print("\n❌ 로컬 개발 환경 요구사항을 충족하지 않습니다.")
        print("📖 자세한 설정 방법은 .cursor/rules/development.md를 참조하세요.")
        sys.exit(1)
    
    # 키움 API 테스트 모드
    if args.kiwoom_test:
        if test_kiwoom_connection():
            print("\n✅ 키움 API 연결 테스트가 성공했습니다!")
            sys.exit(0)
        else:
            print("\n❌ 키움 API 연결 테스트에 실패했습니다.")
            sys.exit(1)
    
    # 시스템 테스트 모드
    if args.test:
        graph_ok = test_graph()
        kiwoom_ok = test_kiwoom_connection()
        
        if graph_ok and kiwoom_ok:
            print("\n✅ 모든 테스트가 통과했습니다!")
            print("🚀 서버를 시작할 준비가 완료되었습니다.")
            sys.exit(0)
        else:
            print("\n❌ 일부 테스트에 실패했습니다.")
            if not graph_ok:
                print("   • LangGraph 테스트 실패")
            if not kiwoom_ok:
                print("   • 키움 API 연결 테스트 실패")
            print("📖 문제 해결 방법은 .cursor/rules/troubleshooting.md를 참조하세요.")
            sys.exit(1)
    
    # 서버 실행
    if args.legacy:
        run_legacy_server(args)
    else:
        run_supervisor_server(args)


if __name__ == "__main__":
    main() 