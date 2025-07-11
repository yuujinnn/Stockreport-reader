#!/usr/bin/env python3
"""
LangGraph 기반 Supervisor 멀티 에이전트 시스템
메인 서버 스크립트

이 스크립트는 주식 분석을 위한 멀티 에이전트 시스템을 실행합니다:
- Supervisor Agent: 사용자 질문 분석 및 워커 에이전트 조정
- Stock Price Agent: 키움증권 API를 통한 주식 데이터 조회

Architecture: LangGraph Supervisor MAS
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
    """시스템 정보 출력"""
    print("=" * 60)
    print("🤖 LangGraph Supervisor MAS for Stock Analysis")
    print("=" * 60)
    print(f"📊 Architecture: Supervisor Multi-Agent System")
    print(f"🔧 Framework: LangGraph + LangChain")
    print(f"🧠 LLM Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"📈 Data Source: Kiwoom Securities REST API")
    
    # LangSmith 정보 (LANGSMITH_API_KEY 사용)
    if os.getenv('LANGSMITH_API_KEY'):
        project = os.getenv('LANGSMITH_PROJECT', 'MiraeAssetAI')
        print(f"📊 LangSmith: Enabled (Project: {project})")
        print(f"🔗 Dashboard: https://smith.langchain.com/")
    else:
        print(f"📊 LangSmith: Disabled")
    
    print("\n🔧 Agent Configuration:")
    print(f"  • Supervisor Agent: Query analysis & coordination")
    print(f"  • Stock Price Agent: Kiwoom API data collection")
    print("=" * 60)


def check_requirements():
    """필수 의존성 및 환경변수 확인"""
    print("🔍 시스템 요구사항 확인 중...")
    
    # 환경변수 확인
    required_env_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 누락된 환경변수: {', '.join(missing_vars)}")
        print("📝 secrets/.env 파일에 다음 변수들을 설정해주세요:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
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
        print("💡 다음 명령어로 설치해주세요:")
        print("   pip install -r requirements.txt")
        return False


def run_supervisor_server(args):
    """Supervisor API 서버 실행"""
    from agents.supervisor.api import run_supervisor_server
    
    print("\n🚀 Supervisor API 서버를 시작합니다...")
    print(f"📡 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"📱 API Documentation: http://{args.host}:{args.port}/docs")
    print("=" * 60)
    
    try:
        run_supervisor_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\n👋 서버가 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 오류: {e}")
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
        return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="LangGraph 기반 Supervisor 멀티 에이전트 주식 분석 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시 사용법:
  python main_supervisor.py                    # Supervisor MAS 서버 실행
  python main_supervisor.py --legacy           # Legacy 단일 에이전트 실행
  python main_supervisor.py --test             # 시스템 테스트
  python main_supervisor.py --port 8080        # 포트 8080으로 실행
  python main_supervisor.py --host 127.0.0.1   # 로컬호스트만 접근 허용
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
    
    # 서버 설정
    parser.add_argument(
        '--host',
        default=os.getenv('SERVER_HOST', '0.0.0.0'),
        help='서버 호스트 주소 (기본값: 0.0.0.0)'
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
        help='개발 모드 (파일 변경시 자동 재시작)'
    )
    
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='reload 비활성화'
    )
    
    args = parser.parse_args()
    
    # --no-reload 옵션 처리
    if args.no_reload:
        args.reload = False
    
    # 시스템 정보 출력
    print_system_info()
    
    # 요구사항 확인
    if not check_requirements():
        print("\n❌ 시스템 요구사항을 충족하지 않습니다.")
        sys.exit(1)
    
    # 테스트 모드
    if args.test:
        if test_graph():
            print("\n✅ 모든 테스트가 통과했습니다!")
            sys.exit(0)
        else:
            print("\n❌ 테스트에 실패했습니다.")
            sys.exit(1)
    
    # 서버 실행
    if args.legacy:
        run_legacy_server(args)
    else:
        run_supervisor_server(args)


if __name__ == "__main__":
    main() 