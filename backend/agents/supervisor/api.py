"""
Supervisor Agent FastAPI 서버
ChatClovaX 기반 멀티 에이전트 시스템의 메인 엔드포인트
"""

import os
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from ..shared.graph import create_supervisor_graph, create_initial_state, extract_final_answer, get_graph_status

# 환경변수 로드
load_dotenv("secrets/.env")

# FastAPI 앱 생성
app = FastAPI(
    title="Stock Analysis Supervisor API (ChatClovaX)",
    description="ChatClovaX 기반 LangGraph 멀티 에이전트 주식 분석 시스템",
    version="3.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 그래프 인스턴스
supervisor_graph = None


class QueryRequest(BaseModel):
    """질의 요청 모델"""
    query: str = Field(description="사용자의 주식 관련 질문")
    session_id: Optional[str] = Field(None, description="세션 ID (선택사항)")


class QueryResponse(BaseModel):
    """질의 응답 모델"""
    success: bool
    answer: str
    session_id: Optional[str] = None
    processing_time: Optional[float] = None
    langsmith_url: Optional[str] = None
    metadata: Optional[Dict] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 그래프 초기화"""
    global supervisor_graph
    
    try:
        # 환경변수 확인
        clova_api_key = os.getenv('CLOVASTUDIO_API_KEY')
        if not clova_api_key:
            raise ValueError("CLOVASTUDIO_API_KEY가 설정되지 않았습니다.")
        
        # LangSmith 설정 확인
        langsmith_key = os.getenv('LANGSMITH_API_KEY')
        if langsmith_key:
            # LangChain이 인식할 수 있도록 환경변수 설정
            os.environ["LANGCHAIN_API_KEY"] = langsmith_key
            os.environ["LANGCHAIN_TRACING_V2"] = os.getenv('LANGSMITH_TRACING', 'true')
            os.environ["LANGCHAIN_ENDPOINT"] = os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
            os.environ["LANGCHAIN_PROJECT"] = os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis')
            
            print("✅ LangSmith 추적이 활성화되었습니다.")
            project = os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis')
            print(f"📊 프로젝트: {project}")
        else:
            print("ℹ️  LangSmith 추적이 비활성화되었습니다.")
        
        # ChatClovaX 기반 Supervisor 그래프 생성
        supervisor_graph = create_supervisor_graph()
        print("🤖 ChatClovaX 기반 Supervisor 멀티 에이전트 시스템이 초기화되었습니다.")
        
        # 시스템 상태 출력
        status = get_graph_status()
        print(f"🏗️  시스템: {status['system']}")
        print(f"🧠 모델: {status['supervisor_model']}")
        print(f"👥 워커 에이전트: {', '.join(status['worker_agents'])}")
        
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        raise


@app.get("/")
async def root():
    """루트 엔드포인트"""
    status = get_graph_status()
    
    return {
        "name": "Stock Analysis Supervisor API (ChatClovaX)",
        "version": "3.0.0",
        "description": "ChatClovaX 기반 LangGraph 멀티 에이전트 주식 분석 시스템",
        "system_info": status,
        "endpoints": {
            "POST /query": "주식 관련 질문 처리",
            "GET /health": "시스템 상태 확인",
            "GET /status": "상세 시스템 정보"
        },
        "key_features": [
            "ChatClovaX HCX-005 기반 AI 분석",
            "langgraph-supervisor 패턴",
            "키움증권 API 연동",
            "실시간 주가 데이터 분석"
        ]
    }


@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    global supervisor_graph
    
    clova_api_key = os.getenv('CLOVASTUDIO_API_KEY')
    status = get_graph_status()
    
    return {
        "status": "healthy" if supervisor_graph and clova_api_key else "unhealthy",
        "graph_initialized": supervisor_graph is not None,
        "clova_api_available": clova_api_key is not None,
        "langsmith_enabled": os.getenv('LANGSMITH_API_KEY') is not None,
        "langsmith_project": os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis'),
        "system_status": status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def system_status():
    """상세 시스템 상태 정보"""
    status = get_graph_status()
    
    return {
        "system_details": status,
        "environment": {
            "clova_api_configured": os.getenv('CLOVASTUDIO_API_KEY') is not None,
            "langsmith_configured": os.getenv('LANGSMITH_API_KEY') is not None,
            "langsmith_project": os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis'),
            "kiwoom_api_configured": True  # Stock Price Agent에서 관리
        },
        "runtime_info": {
            "graph_compiled": supervisor_graph is not None,
            "startup_time": os.getenv("REQUEST_TIME", "unknown"),
            "current_time": datetime.now().isoformat()
        }
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    사용자의 주식 관련 질문을 처리합니다
    
    Args:
        request: 질의 요청
        
    Returns:
        QueryResponse: 처리 결과
    """
    global supervisor_graph
    
    if not supervisor_graph:
        raise HTTPException(
            status_code=500,
            detail="Supervisor 그래프가 초기화되지 않았습니다."
        )
    
    start_time = datetime.now()
    
    try:
        # 초기 상태 생성
        os.environ["REQUEST_TIME"] = start_time.isoformat()
        initial_state = create_initial_state(request.query)
        
        # 세션 ID 처리
        if request.session_id:
            initial_state["metadata"] = initial_state.get("metadata", {})
            initial_state["metadata"]["session_id"] = request.session_id
        
        # LangSmith 추적 설정
        langsmith_url = None
        if os.getenv('LANGSMITH_API_KEY'):
            project = os.getenv('LANGSMITH_PROJECT', 'ChatClovaX_StockAnalysis')
            run_name = f"clovax_supervisor_{start_time.strftime('%Y%m%d_%H%M%S')}"
            os.environ["LANGCHAIN_RUN_NAME"] = run_name
            
            base_url = "https://smith.langchain.com"
            langsmith_url = f"{base_url}/public/{project}/r"
        
        # 그래프 실행
        print(f"📝 사용자 질문: {request.query}")
        print(f"🤖 ChatClovaX Supervisor 시스템 처리 시작...")
        
        final_state = supervisor_graph.invoke(initial_state)
        
        # 최종 답변 추출
        answer = extract_final_answer(final_state)
        
        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 메타데이터 수집
        metadata = final_state.get("metadata", {})
        metadata["processing_time"] = processing_time
        metadata["message_count"] = len(final_state.get("messages", []))
        metadata["system"] = "ChatClovaX_Supervisor"
        
        print(f"✅ 처리 완료 ({processing_time:.2f}초)")
        
        return QueryResponse(
            success=True,
            answer=answer,
            session_id=request.session_id,
            processing_time=processing_time,
            langsmith_url=langsmith_url,
            metadata=metadata
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"ChatClovaX Supervisor 처리 중 오류: {str(e)}"
        
        print(f"❌ {error_msg}")
        
        return QueryResponse(
            success=False,
            answer="처리 중 오류가 발생했습니다. 다시 시도해주세요.",
            session_id=request.session_id,
            processing_time=processing_time,
            error=error_msg
        )


# 개발용 실행 함수
def run_supervisor_server(host: str = None, port: int = None, reload: bool = None):
    """Supervisor API 서버 실행"""
    if host is None:
        host = os.getenv('SERVER_HOST', '0.0.0.0')
    if port is None:
        port = int(os.getenv('SERVER_PORT', '8000'))
    if reload is None:
        reload = os.getenv('SERVER_RELOAD', 'true').lower() == 'true'
    
    print(f"🚀 ChatClovaX Supervisor API 서버 시작")
    print(f"🌐 주소: http://{host}:{port}")
    
    uvicorn.run(
        "agents.supervisor.api:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_supervisor_server() 