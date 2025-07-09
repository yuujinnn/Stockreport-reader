"""
주식 차트 데이터 조회 에이전트 서버 실행
"""
import os
from dotenv import load_dotenv
from stock_price.api import run_server

# 환경변수 로드
load_dotenv()

if __name__ == "__main__":
    print("에이전트 서버를 시작합니다.")
    print("API 문서: http://localhost:8000/docs")
    print("서버 주소: http://localhost:8000")
    
    # OpenAI API 키 확인
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   API 요청 시 openai_api_key 파라미터를 제공해야 합니다.")
    else:
        print("OpenAI API 키가 확인되었습니다.")
    
    # LangSmith API 키 확인
    langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
    if not langchain_api_key:
        print("LANGCHAIN_API_KEY 환경변수가 설정되지 않았습니다.")
    else:
        print("LangSmith API 키가 확인되었습니다.")
    
    # 서버 실행
    run_server(
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 