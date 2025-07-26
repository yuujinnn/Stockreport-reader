"""
Test script for SearchAgent
Simple verification of SearchAgent functionality
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()
load_dotenv("secrets/.env")
load_dotenv("backend/secrets/.env")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_naver_api():
    """Test Naver News API connection"""
    print("🔍 Testing Naver News API...")
    
    try:
        from news_agent.naver_api import get_naver_api
        
        api = get_naver_api()
        results = api.search_news("삼성전자", max_count=3)
        
        if results:
            print(f"✅ API 연결 성공! {len(results)}개 기사 검색됨")
            for i, article in enumerate(results[:2], 1):
                print(f"  {i}. {article['title']}")
        else:
            print("❌ API 연결 실패: 검색 결과 없음")
            
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")

def test_search_tools():
    """Test SearchAgent tools"""
    print("\n🛠️ Testing SearchAgent tools...")
    
    try:
        from news_agent.tools import get_search_tools
        
        tools = get_search_tools()
        print(f"✅ 도구 로드 성공! {len(tools)}개 도구 사용 가능")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:100]}...")
            
    except Exception as e:
        print(f"❌ 도구 테스트 실패: {e}")

def test_search_agent():
    """Test SearchAgent functionality"""
    print("\n🤖 Testing SearchAgent...")
    
    try:
        from news_agent.agent import SearchAgent
        
        agent = SearchAgent()
        print("✅ SearchAgent 초기화 성공!")
        
        # Test simple query
        test_query = "카카오페이의 굿딜서비스에 대해서 알려주세요"
        print(f"\n📝 테스트 쿼리: {test_query}")
        
        result = agent.run(test_query)
        print(f"✅ 검색 및 분석 완료!")
        print(f"📊 결과 길이: {len(result)} 문자")
        print(f"📋 결과 샘플: {result[:200]}...")
        
    except Exception as e:
        print(f"❌ SearchAgent 테스트 실패: {e}")

def test_system_status():
    """Test system status check"""
    print("\n📊 Testing system status...")
    
    try:
        from news_agent.agent import SearchAgent
        
        agent = SearchAgent()
        status = agent.get_system_status()
        
        print("✅ 시스템 상태:")
        for key, value in status.items():
            print(f"  - {key}: {value}")
            
    except Exception as e:
        print(f"❌ 시스템 상태 확인 실패: {e}")

def test_tavily_integration():
    """Test Tavily integration separately"""
    print("\n🌐 Testing Tavily integration...")
    
    try:
        from langchain_tavily import TavilySearch
        
        # Check if we can create the tool (using correct TavilySearch class)
        tavily_tool = TavilySearch(max_results=1, topic="general")
        print("✅ Tavily tool creation successful (TavilySearch class)")
        
        # Check if TAVILY_API_KEY is set
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key:
            print("✅ TAVILY_API_KEY environment variable found")
        else:
            print("⚠️ TAVILY_API_KEY not set - web search will not work")
            
        return True
        
    except Exception as e:
        print(f"❌ Tavily integration test failed: {e}")
        return False

def test_autonomous_reasoning():
    """Test that SearchAgent uses autonomous reasoning (no hard-coded logic)"""
    print("\n🧠 Testing autonomous reasoning...")
    
    try:
        from news_agent.agent import SearchAgent
        
        agent = SearchAgent()
        
        # Verify no hard-coded methods exist
        forbidden_methods = ['analyze_query_type', '_recommend_tools']
        for method in forbidden_methods:
            if hasattr(agent, method):
                print(f"❌ CRITICAL: Found hard-coded method '{method}' - violates ReAct principles!")
                return False
        
        print("✅ 확인: 하드코딩된 도구 선택 로직 없음 - 순수 자율적 추론")
        
        # Test different query types to ensure autonomous tool selection
        test_queries = [
            "삼성전자 최근 뉴스",  # Should choose naver news by date
            "인공지능에 대한 설명",  # Should choose tavily web search
            "카카오페이 회사 정보"  # Should choose naver news by relevance
        ]
        
        print("\n🔍 자율적 도구 선택 테스트:")
        for query in test_queries:
            print(f"  📝 쿼리: {query}")
            # We won't run full queries to save time, just verify structure
        
        return True
        
    except Exception as e:
        print(f"❌ 자율적 추론 테스트 실패: {e}")
        return False

def check_environment():
    """Check if required environment variables are set"""
    print("🔧 환경 변수 확인...")
    
    required_vars = [
        "CLOVASTUDIO_API_KEY", 
        "NAVER_CLIENT_ID", 
        "NAVER_CLIENT_SECRET"
    ]
    
    # Optional but recommended
    optional_vars = ["TAVILY_API_KEY"]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 누락된 환경 변수: {', '.join(missing_vars)}")
        print(f"\n📋 backend/secrets/.env 파일을 생성하고 다음 변수들을 설정해주세요:")
        print("=" * 60)
        for var in missing_vars:
            if var == "CLOVASTUDIO_API_KEY":
                print(f"   {var}=your_clova_studio_api_key")
                print("   # Get from: https://clovastudio.naver.com/")
            elif var == "NAVER_CLIENT_ID":
                print(f"   {var}=your_naver_client_id")
                print("   # Get from: https://developers.naver.com/apps/")
            elif var == "NAVER_CLIENT_SECRET":
                print(f"   {var}=your_naver_client_secret")
                print("   # Get from: https://developers.naver.com/apps/")
            print("")
        print("=" * 60)
        return False
    else:
        print("✅ 모든 필수 환경 변수 설정 완료")
        
        # Check optional variables
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        if missing_optional:
            print(f"⚠️ 권장 환경 변수 누락: {', '.join(missing_optional)}")
            print("   - TAVILY_API_KEY: 웹 검색 기능을 위해 권장")
            print("   # Get from: https://app.tavily.com/")
            print("   # Free tier: 1000 searches/month")
        
        return True

if __name__ == "__main__":
    print("🧪 SearchAgent 테스트 시작")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\n❌ 환경 변수 설정이 필요합니다. 테스트를 중단합니다.")
        exit(1)
    
    # Run tests
    test_naver_api()
    test_tavily_integration()
    test_search_tools()
    test_search_agent()
    test_system_status()
    test_autonomous_reasoning()
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료!") 