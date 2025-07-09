"""
주식 차트 데이터 조회 에이전트 FastAPI 서버
"""
import os
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from .agent import create_stock_agent, StockPriceAgent

# secrets/.env 파일에서 환경변수 로드
load_dotenv("secrets/.env")

# FastAPI 앱 설정값들을 환경변수에서 로드
app_title = os.getenv('FASTAPI_TITLE', 'Stock Price Agent API')
app_description = os.getenv('FASTAPI_DESCRIPTION', '주식 차트 데이터 조회 에이전트 API')
app_version = os.getenv('FASTAPI_VERSION', '1.0.0')

# FastAPI 앱 생성
app = FastAPI(
    title=app_title,
    description=app_description,
    version=app_version
)

# CORS 설정도 환경변수에서 로드
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
cors_credentials = os.getenv('CORS_CREDENTIALS', 'true').lower() == 'true'
cors_methods = os.getenv('CORS_METHODS', '*').split(',')
cors_headers = os.getenv('CORS_HEADERS', '*').split(',')

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# 전역 에이전트 인스턴스
agent: Optional[StockPriceAgent] = None


class QueryRequest(BaseModel):
    """질의 요청 모델"""
    query: str
    openai_api_key: Optional[str] = None


class QueryResponse(BaseModel):
    """질의 응답 모델"""
    success: bool
    output: str
    intermediate_steps: Optional[list] = None
    error: Optional[str] = None
    run_name: Optional[str] = None
    langsmith_url: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 에이전트 초기화"""
    global agent
    try:
        # OpenAI API 키 확인
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            agent = create_stock_agent(openai_api_key)
            print("주식 차트 에이전트가 초기화되었습니다.")
        else:
            print("OPENAI_API_KEY가 설정되지 않았습니다. 요청시 API 키를 제공해야 합니다.")
        
        # LangSmith 상태 확인
        langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
        langsmith_project = os.getenv('LANGSMITH_PROJECT', 'stock-price-agent')
        
        if langchain_api_key:
            print("LangSmith 추적이 활성화되었습니다.")
            print(f"프로젝트: {langsmith_project}")
            print(f"대시보드: https://smith.langchain.com/")
        else:
            print("LANGCHAIN_API_KEY가 설정되지 않았습니다. LangSmith 추적이 비활성화됩니다.")
            
    except Exception as e:
        print(f"에이전트 초기화 실패: {e}")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": app_description,
        "version": app_version,
        "endpoints": {
            "POST /query": "주식 데이터 조회",
            "POST /clear": "대화 메모리 초기화",
            "GET /health": "서버 상태 확인"
        }
    }


@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    langsmith_project = os.getenv('LANGSMITH_PROJECT', 'stock-price-agent')
    
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "langsmith_enabled": os.getenv('LANGCHAIN_API_KEY') is not None,
        "langsmith_project": langsmith_project if os.getenv('LANGCHAIN_API_KEY') else None
    }


@app.post("/query", response_model=QueryResponse)
async def query_stock_data(request: QueryRequest):
    """
    주식 차트 데이터 조회
    
    Args:
        request: 질의 요청 (query, openai_api_key)
        
    Returns:
        QueryResponse: 처리 결과
    """
    global agent
    
    try:
        # 에이전트가 초기화되지 않았거나 API 키가 제공된 경우
        if not agent or request.openai_api_key:
            api_key = request.openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail="OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 요청에 포함하세요."
                )
            agent = create_stock_agent(api_key)
        
        # 에이전트 질의 실행
        result = agent.query(request.query)
        
        # LangSmith URL 생성
        langsmith_url = None
        langsmith_project = os.getenv('LANGSMITH_PROJECT', 'stock-price-agent')
        langsmith_base_url = os.getenv('LANGSMITH_BASE_URL', 'https://smith.langchain.com/public')
        
        if result.get("run_name") and os.getenv('LANGCHAIN_API_KEY'):
            langsmith_url = f"{langsmith_base_url}/{langsmith_project}/r"
        
        return QueryResponse(
            success=result["success"],
            output=result["output"],
            intermediate_steps=result.get("intermediate_steps"),
            error=result.get("error"),
            run_name=result.get("run_name"),
            langsmith_url=langsmith_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear_memory():
    """대화 메모리 초기화"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=400, detail="에이전트가 초기화되지 않았습니다.")
    
    agent.clear_memory()
    return {"message": "대화 메모리가 초기화되었습니다."}


@app.get("/examples")
async def get_examples():
    """사용 예시 반환"""
    return {
        "examples": [
            {
                "description": "삼성전자 2024년 주봉 데이터 조회",
                "query": "2024년 1년간 삼성전자의 주봉 데이터를 알려주세요"
            },
            {
                "description": "SK하이닉스 최근 3개월 일봉 데이터 조회",
                "query": "SK하이닉스 최근 3개월 일봉 차트 데이터를 가져와주세요"
            },
            {
                "description": "NAVER 1분봉 데이터 조회",
                "query": "네이버 1분봉 차트 데이터를 조회해주세요"
            },
            {
                "description": "카카오 월봉 데이터 조회",
                "query": "카카오 2023년부터 지금까지 월봉 데이터를 받아주세요"
            }
        ],
        "supported_stocks": {
            "삼성전자": "005930",
            "SK하이닉스": "000660",
            "NAVER": "035420",
            "카카오": "035720",
            "LG화학": "051910",
            "현대차": "005380",
            "기아": "000270",
            "포스코홀딩스": "005490"
        },
        "chart_types": [
            "틱차트 (초단위)",
            "분봉차트 (1, 3, 5, 10, 15, 30, 45, 60분)",
            "일봉차트",
            "주봉차트",
            "월봉차트",
            "년봉차트"
        ]
    }


# 개발용 실행 함수
def run_server(host: str = None, port: int = None, reload: bool = None):
    """개발용 서버 실행"""
    # 서버 설정값들도 환경변수에서 로드
    if host is None:
        host = os.getenv('SERVER_HOST', '0.0.0.0')
    if port is None:
        port = int(os.getenv('SERVER_PORT', '8000'))
    if reload is None:
        reload = os.getenv('SERVER_RELOAD', 'true').lower() == 'true'
    
    uvicorn.run(
        "stock_price.api:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server() 