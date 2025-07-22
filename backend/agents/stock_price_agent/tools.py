"""
Simplified LangChain tools for ChatClovaX agent
Returns pandas DataFrames with upgrade suggestions when needed
"""

import pandas as pd
from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .kiwoom_api import (
    get_minute_chart, get_day_chart, 
    get_week_chart, get_month_chart, get_year_chart
)
from .data_manager import get_data_manager
from .utils import get_today_date


class MinuteChartInput(BaseModel):
    stock_code: str = Field(description="6-digit stock code (e.g., 005930)")
    minute_scope: str = Field(description="Minute scope (1, 3, 5, 10, 15, 30, 45, 60)")
    expected_start_date: Optional[str] = Field(None, description="Expected start date (YYYYMMDD)")
    expected_end_date: Optional[str] = Field(None, description="Expected end date (YYYYMMDD)")


class DayChartInput(BaseModel):
    stock_code: str = Field(description="6-digit stock code (e.g., 005930)")
    expected_start_date: Optional[str] = Field(None, description="Expected start date (YYYYMMDD)")
    expected_end_date: Optional[str] = Field(None, description="Expected end date (YYYYMMDD)")


class WeekChartInput(BaseModel):
    stock_code: str = Field(description="6-digit stock code (e.g., 005930)")
    expected_start_date: Optional[str] = Field(None, description="Expected start date (YYYYMMDD)")
    expected_end_date: Optional[str] = Field(None, description="Expected end date (YYYYMMDD)")


class MonthChartInput(BaseModel):
    stock_code: str = Field(description="6-digit stock code (e.g., 005930)")
    expected_start_date: Optional[str] = Field(None, description="Expected start date (YYYYMMDD)")
    expected_end_date: Optional[str] = Field(None, description="Expected end date (YYYYMMDD)")


class YearChartInput(BaseModel):
    stock_code: str = Field(description="6-digit stock code (e.g., 005930)")
    expected_start_date: Optional[str] = Field(None, description="Expected start date (YYYYMMDD)")
    expected_end_date: Optional[str] = Field(None, description="Expected end date (YYYYMMDD)")


class MinuteChartTool(BaseTool):
    name: str = "get_minute_chart"
    description: str = "주식 분봉차트 조회 (1, 3, 5, 10, 15, 30, 45, 60분 범위). 단기 트레이딩 및 일중 패턴 분석용으로 1일~1주일 기간에 적합."
    args_schema: type = MinuteChartInput

    def _run(self, stock_code: str, minute_scope: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        try:
            raw_data = get_minute_chart(stock_code, minute_scope)
            if not raw_data:
                return "Failed to fetch minute chart data"
            
            data_manager = get_data_manager()
            result = data_manager.process_chart_data(
                raw_data, stock_code, "minute", None, expected_start_date, expected_end_date, minute_scope
            )
            
            # Use unified formatting function from data_manager
            return data_manager.format_tool_response(result, stock_code, f"{minute_scope}-minute")
            
        except Exception as e:
            return f"Error fetching minute chart: {str(e)}"


class DayChartTool(BaseTool):
    name: str = "get_day_chart" 
    description: str = "주식 일봉차트 조회. 중단기 분석의 표준으로 1주일~1년 기간의 일반적인 기술적 분석에 가장 적합. 기준일자 역순으로 과거 데이터 조회."
    args_schema: type = DayChartInput

    def _run(self, stock_code: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        # Use expected_end_date as base_date, fallback to today if not provided
        base_date = expected_end_date if expected_end_date else get_today_date()
            
        try:
            raw_data = get_day_chart(stock_code, base_date)
            if not raw_data:
                return "Failed to fetch daily chart data"
            
            data_manager = get_data_manager()
            result = data_manager.process_chart_data(
                raw_data, stock_code, "day", base_date, expected_start_date, expected_end_date, None
            )
            
            # Use unified formatting function from data_manager
            return data_manager.format_tool_response(result, stock_code, "daily")
            
        except Exception as e:
            return f"Error fetching daily chart: {str(e)}"


class WeekChartTool(BaseTool):
    name: str = "get_week_chart"
    description: str = "주식 주봉차트 조회. 중장기 트렌드 및 패턴 분석용으로 1개월~5년 기간의 거시적 흐름 파악에 적합. 노이즈 제거된 안정적 패턴 확인 가능."
    args_schema: type = WeekChartInput

    def _run(self, stock_code: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        # Use expected_end_date as base_date, fallback to today if not provided
        base_date = expected_end_date if expected_end_date else get_today_date()
            
        try:
            raw_data = get_week_chart(stock_code, base_date)
            if not raw_data:
                return "Failed to fetch weekly chart data"
            
            data_manager = get_data_manager()
            result = data_manager.process_chart_data(
                raw_data, stock_code, "week", base_date, expected_start_date, expected_end_date, None
            )
            
            # Use unified formatting function from data_manager
            return data_manager.format_tool_response(result, stock_code, "weekly")
            
        except Exception as e:
            return f"Error fetching weekly chart: {str(e)}"


class MonthChartTool(BaseTool):
    name: str = "get_month_chart"
    description: str = "주식 월봉차트 조회. 장기 트렌드 및 펀더멘털 분석용으로 6개월~10년 기간의 거시경제 영향과 기업 실적 반영 패턴 확인에 적합."
    args_schema: type = MonthChartInput

    def _run(self, stock_code: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        # Use expected_end_date as base_date, fallback to today if not provided
        base_date = expected_end_date if expected_end_date else get_today_date()
            
        try:
            raw_data = get_month_chart(stock_code, base_date)
            if not raw_data:
                return "Failed to fetch monthly chart data"
            
            data_manager = get_data_manager()
            result = data_manager.process_chart_data(
                raw_data, stock_code, "month", base_date, expected_start_date, expected_end_date, None
            )
            
            # Use unified formatting function from data_manager
            return data_manager.format_tool_response(result, stock_code, "monthly")
            
        except Exception as e:
            return f"Error fetching monthly chart: {str(e)}"


class YearChartTool(BaseTool):
    name: str = "get_year_chart"
    description: str = "주식 년봉차트 조회. 초장기 히스토리 분석용으로 5년 이상의 역사적 패턴, 경기 사이클, 구조적 변화 분석에 적합. 장기 투자 관점에서 사용."
    args_schema: type = YearChartInput

    def _run(self, stock_code: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        # Use expected_end_date as base_date, fallback to today if not provided
        base_date = expected_end_date if expected_end_date else get_today_date()
            
        try:
            raw_data = get_year_chart(stock_code, base_date)
            if not raw_data:
                return "Failed to fetch yearly chart data"
            
            data_manager = get_data_manager()
            result = data_manager.process_chart_data(
                raw_data, stock_code, "year", base_date, expected_start_date, expected_end_date, None
            )
            
            # Use unified formatting function from data_manager
            return data_manager.format_tool_response(result, stock_code, "yearly")
            
        except Exception as e:
            return f"Error fetching yearly chart: {str(e)}"


def get_stock_tools():
    """Get list of stock chart tools"""
    return [
        MinuteChartTool(),
        DayChartTool(), 
        WeekChartTool(),
        MonthChartTool(),
        YearChartTool()
    ] 