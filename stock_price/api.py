"""
주식 차트 데이터 조회 에이전트 FastAPI 서버
"""
import os
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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


class DataRequest(BaseModel):
    """오케스트레이터로부터의 데이터 요청 모델"""
    tickers: List[str] = Field(description="종목 코드 리스트 (예: ['377300.KS', '005930.KS'])")
    from_date: str = Field(alias="from", description="시작 날짜 (YYYYMMDD, ALL, NONE)")
    to_date: str = Field(alias="to", description="종료 날짜 (YYYYMMDD, ALL, NONE)")
    interval: str = Field(description="차트 간격 (AUTO, D, W, M, Y, 1, 5, 15, 30, 60)")
    openai_api_key: Optional[str] = None


class QueryResponse(BaseModel):
    """질의 응답 모델"""
    success: bool
    output: str
    intermediate_steps: Optional[list] = None
    error: Optional[str] = None
    run_name: Optional[str] = None
    langsmith_url: Optional[str] = None


class DataResponse(BaseModel):
    """데이터 응답 모델"""
    success: bool
    data: Optional[Dict] = None
    tickers_processed: Optional[List[str]] = None
    chart_type: Optional[str] = None
    date_range: Optional[Dict] = None
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
            "POST /data": "오케스트레이터로부터 구조화된 데이터 요청 처리",
            "POST /query": "자연어 질의 처리 (호환성용)",
            "POST /clear": "대화 메모리 초기화",
            "GET /health": "서버 상태 확인",
            "GET /examples": "사용 예시"
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


@app.post("/data", response_model=DataResponse)
async def collect_chart_data(request: DataRequest):
    """
    오케스트레이터로부터 구조화된 데이터 요청을 받아 차트 데이터 수집
    
    Args:
        request: 데이터 요청 (tickers, from, to, interval)
        
    Returns:
        DataResponse: 수집된 데이터
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
        
        # 요청을 자연어로 변환하여 에이전트에 전달
        query_text = f"""
다음 구조화된 데이터 요청을 처리해주세요:

종목: {', '.join(request.tickers)}
시작일: {request.from_date}
종료일: {request.to_date}
차트 간격: {request.interval}

모든 종목에 대해 지정된 기간과 간격에 맞는 차트 데이터를 수집하고,
완전한 JSON 형식으로 반환해주세요.
"""
        
        # 에이전트 실행
        result = agent.query(query_text)
        
        # LangSmith URL 생성
        langsmith_url = None
        langsmith_project = os.getenv('LANGSMITH_PROJECT', 'stock-price-agent')
        langsmith_base_url = os.getenv('LANGSMITH_BASE_URL', 'https://smith.langchain.com/public')
        
        if result.get("run_name") and os.getenv('LANGCHAIN_API_KEY'):
            langsmith_url = f"{langsmith_base_url}/{langsmith_project}/r"
        
        # 성공 응답
        if result["success"]:
            # 티커를 키움 API 형식으로 변환
            from .utils import get_ticker_manager
            ticker_manager = get_ticker_manager()
            processed_tickers = ticker_manager.convert_multiple_tickers(request.tickers)
            
            return DataResponse(
                success=True,
                data={"chart_data": result["output"]},
                tickers_processed=processed_tickers,
                chart_type=request.interval,
                date_range={
                    "from": request.from_date,
                    "to": request.to_date
                },
                run_name=result.get("run_name"),
                langsmith_url=langsmith_url
            )
        else:
            return DataResponse(
                success=False,
                error=result.get("error", "데이터 수집 실패"),
                run_name=result.get("run_name"),
                langsmith_url=langsmith_url
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        "data_request_examples": [
            {
                "description": "삼성전자 2024년 일봉 데이터 자동 선택",
                "request": {
                    "tickers": ["005930.KS"],
                    "from": "20240101",
                    "to": "20241231",
                    "interval": "AUTO"
                }
            },
            {
                "description": "카카오와 네이버 최근 1개월 주봉 데이터",
                "request": {
                    "tickers": ["035720.KS", "035420.KS"],
                    "from": "20241201",
                    "to": "20250120",
                    "interval": "W"
                }
            },
            {
                "description": "SK하이닉스 역대 전체 월봉 데이터",
                "request": {
                    "tickers": ["000660.KS"],
                    "from": "ALL",
                    "to": "ALL",
                    "interval": "M"
                }
            },
            {
                "description": "현대차 최근 데이터 5분봉",
                "request": {
                    "tickers": ["005380.KS"],
                    "from": "NONE",
                    "to": "NONE",
                    "interval": "5"
                }
            }
        ],
        "legacy_query_examples": [
            {
                "description": "자연어 질의 (호환성용)",
                "query": "2024년 1년간 삼성전자의 주봉 데이터를 알려주세요"
            }
        ],
        "supported_intervals": {
            "AUTO": "기간에 맞는 최적 차트 자동 선택",
            "D": "일봉",
            "W": "주봉",
            "M": "월봉",
            "Y": "년봉",
            "1": "1분봉",
            "5": "5분봉",
            "15": "15분봉",
            "30": "30분봉",
            "60": "60분봉"
        },
        "date_formats": {
            "YYYYMMDD": "명확한 날짜 (예: 20240101)",
            "ALL": "역대 전체 데이터",
            "NONE": "최근 데이터만 (약 300개 레코드)"
        },
        "ticker_formats": {
            "KS": "코스피 종목 (예: 005930.KS)",
            "KQ": "코스닥 종목 (예: 377300.KQ)",
            "note": "거래소 접미사(.KS, .KQ)는 자동으로 제거됩니다"
        },
        "supported_stocks": {
            "삼성전자": "005930.KS",
            "SK하이닉스": "000660.KS",
            "NAVER": "035420.KS",
            "카카오": "035720.KS",
            "LG화학": "051910.KS",
            "현대차": "005380.KS",
            "기아": "000270.KS",
            "포스코홀딩스": "005490.KS",
            "카카오게임즈": "293490.KQ",
            "셀트리온헬스케어": "091990.KS"
        }
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