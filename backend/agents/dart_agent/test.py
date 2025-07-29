"""
FastAPI Server for ChatClovaX Stock Price Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

from .agent import DartAgent



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ChatClovaX Stock Price Agent API",
    description="Dart API를 통한 주식 데이터 분석 서비스",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시에는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[DartAgent] = None


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    max_tokens: Optional[int] = 4096
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "삼성전자 최근 1개월 주가 데이터 분석해줘",
                "max_tokens": 4096
            }
        }


class QueryResponse(BaseModel):
    success: bool
    response: str
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "삼성전자(005930)의 최근 1개월 일봉 주가 데이터...",
                "error": None
            }
        }


class HealthResponse(BaseModel):
    status: str
    agent_initialized: bool
    available_tools: List[str]


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    try:
        logger.info("🚀 Initializing ChatClovaX Stock Price Agent...")
        agent = DartAgent()
        logger.info("✅ Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        agent = None


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if agent is not None else "unhealthy",
        agent_initialized=agent is not None,
        available_tools=agent.get_available_tools() if agent else []
    )


# Main query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_stock_data(request: QueryRequest):
    """
    주식 데이터 분석 쿼리 처리
    """
    if agent is None:
        raise HTTPException(
            status_code=503, 
            detail="Agent not initialized. Please check server logs."
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info(f"📥 Processing query: {request.query}")
        
        # Process the query
        response = agent.run(request.query)
        
        logger.info(f"✅ Query processed successfully")
        
        return QueryResponse(
            success=True,
            response=response
        )
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        return QueryResponse(
            success=False,
            response="",
            error=error_msg
        )


# Tools info endpoint
@app.get("/tools")
async def get_available_tools():
    """Get list of available tools"""
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized"
        )
    
    return {
        "tools": agent.get_available_tools(),
        "description": "Available chart data fetching tools"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "ChatClovaX Stock Price Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "tools": "/tools",
            "docs": "/docs"
        }
    }


# Run server
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "agents.stock_price_agent.test:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True) 