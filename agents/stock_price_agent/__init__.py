"""
Stock Price Agent Package (ChatClovaX)
키움증권 REST API를 통한 주식 데이터 조회 - ChatClovaX HCX-005 버전
"""

from .agent import StockPriceAgent, run_agent
from .prompt import STOCK_PRICE_AGENT_PROMPT
from .tools import get_stock_tools
from .data_manager import StockDataManager, get_data_manager
from .kiwoom_api import (
    KiwoomTokenManager, get_token_manager,
    get_minute_chart, get_day_chart, get_week_chart, 
    get_month_chart, get_year_chart
)
from .utils import (
    calculate_date_placeholders, format_prompt_with_dates, get_today_date
)
from .test import app, run_server

__all__ = [
    # Main agent
    "StockPriceAgent",
    "run_agent",
    
    # FastAPI server
    "app",
    "run_server",
    
    # Prompt
    "STOCK_PRICE_AGENT_PROMPT",
    
    # Tools
    "get_stock_tools",
    
    # Data management
    "StockDataManager", 
    "get_data_manager",
    
    # Kiwoom API
    "KiwoomTokenManager",
    "get_token_manager",
    "get_minute_chart",
    "get_day_chart", 
    "get_week_chart",
    "get_month_chart",
    "get_year_chart",
    
    # Date utilities
    "calculate_date_placeholders",
    "format_prompt_with_dates",
    "get_today_date"
] 