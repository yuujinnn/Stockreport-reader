"""
Minimal FastAPI server for SearchAgent (news_agent)
POST /search: receive a query and return the agent's answer
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent import SearchAgent

app = FastAPI(title="Minimal SearchAgent API", description="Simple endpoint for direct SearchAgent queries", version="0.1.0")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

# Single global agent instance (for efficiency)
agent = SearchAgent()

@app.post("/search", response_model=QueryResponse)
def search(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        answer = agent.run(request.query)
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 