"""
공유 상태 정의
LangGraph에서 사용되는 에이전트 간 상태 관리
"""

from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class MessagesState(TypedDict):
    """
    에이전트 간 공유되는 메시지 상태
    
    Attributes:
        messages: 대화 기록 (LangGraph의 add_messages로 관리)
        user_query: 사용자의 원본 질문
        context: 인용된 문서 컨텍스트 정보
        extracted_info: 추출된 정보 (종목, 기간, 차트 유형 등)
        stock_data: Stock Price Agent로부터 받은 주식 데이터
        error: 오류 정보 (있는 경우)
        metadata: 추가 메타데이터
    """
    # 메시지 리스트 (LangGraph 표준)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 사용자 질문 관련
    user_query: Optional[str]
    
    # 인용된 문서 컨텍스트
    context: Optional[str]
    
    # 추출된 정보
    extracted_info: Optional[Dict[str, Any]]
    
    # 주식 데이터
    stock_data: Optional[Dict[str, Any]]
    
    # 오류 정보
    error: Optional[str]
    
    # 메타데이터
    metadata: Optional[Dict[str, Any]]


class ExtractedInfo(TypedDict):
    """
    사용자 질문에서 추출된 정보
    """
    # 종목 정보
    stock_codes: List[str]  # 종목 코드 리스트 (예: ["005930", "377300"])
    stock_names: List[str]  # 종목명 리스트 (예: ["삼성전자", "카카오페이"])
    
    # 기간 정보
    date_range: Dict[str, str]  # {"from": "20250101", "to": "20250331"}
    period_description: str  # "1분기", "3개월간" 등 원본 기간 표현
    
    # 차트 유형
    chart_type: str  # "AUTO", "D", "W", "M", "Y", "1", "5", "15", "30", "60"
    chart_description: str  # "일봉", "주봉" 등 원본 차트 표현
    
    # 분석 목적
    analysis_purpose: str  # "성장세 확인", "변동성 분석" 등
    
    # 신뢰도
    confidence_score: float  # 추출 정보의 신뢰도 (0.0 ~ 1.0) 