"""
키움 API 함수들을 LangChain 툴로 래핑
"""
from typing import Dict, Optional, List, Tuple
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

from .kiwoom import (
    fn_ka10079, fn_ka10080, fn_ka10081, 
    fn_ka10082, fn_ka10083, fn_ka10094,
    save_chart_data_to_json
)
from .utils import get_token_manager

# secrets/.env 파일에서 환경변수 로드
load_dotenv("secrets/.env")

def log_tool_execution(tool_name: str, stock_code: str, params: Dict) -> str:
    """툴 실행 로그를 생성합니다 (LangSmith 추적용)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {tool_name} 실행: 종목={stock_code}, 파라미터={params}"
    
    # LangSmith가 활성화된 경우에만 상세 로그
    if os.getenv('LANGCHAIN_API_KEY'):
        print(f"LangSmith 추적: {log_msg}")
    
    return log_msg


# 데이터 검증 툴
class ChartValidationInput(BaseModel):
    chart_data: str = Field(description="검증할 차트 데이터 (JSON 문자열)")
    expected_start_date: str = Field(description="예상 시작일자 (YYYYMMDD)")
    expected_end_date: str = Field(description="예상 종료일자 (YYYYMMDD)")
    chart_type: str = Field(description="차트 유형 (tick/minute/day/week/month/year)")


class ChartValidationTool(BaseTool):
    name = "validate_chart_data"
    description = "차트 데이터가 예상 날짜 범위를 모두 포함하는지 검증하고, 부족한 데이터가 있으면 추가 호출이 필요한 기준일자를 제안합니다."
    args_schema = ChartValidationInput

    def _run(self, chart_data: str, expected_start_date: str, expected_end_date: str, chart_type: str) -> str:
        try:
            # JSON 파싱
            if isinstance(chart_data, str):
                data = json.loads(chart_data)
            else:
                data = chart_data
            
            result = {
                "is_complete": False,
                "missing_data": False,
                "next_base_date": None,
                "data_count": 0,
                "actual_start_date": None,
                "actual_end_date": None,
                "recommendation": ""
            }
            
            # 키움 API 응답에서 차트 데이터 추출
            chart_records = []
            if 'output2' in data and isinstance(data['output2'], list):
                chart_records = data['output2']
            elif 'stk_stk_pole_chart_qry' in data:
                chart_records = data['stk_stk_pole_chart_qry']
            
            result["data_count"] = len(chart_records)
            
            if not chart_records:
                result["recommendation"] = "데이터가 없습니다. API 호출 파라미터를 확인하세요."
                return json.dumps(result, ensure_ascii=False)
            
            # 실제 데이터 날짜 범위 추출
            dates = []
            for record in chart_records:
                # 키움 API는 보통 'stck_bsop_date' 또는 'date' 필드에 날짜가 있음
                date_field = record.get('stck_bsop_date') or record.get('date') or record.get('dt')
                if date_field:
                    dates.append(date_field)
            
            if dates:
                dates.sort()
                result["actual_start_date"] = dates[-1]  # 키움 API는 최신 날짜부터 역순으로 제공
                result["actual_end_date"] = dates[0]
                
                # 예상 범위와 비교
                expected_start = datetime.strptime(expected_start_date, "%Y%m%d")
                expected_end = datetime.strptime(expected_end_date, "%Y%m%d")
                actual_start = datetime.strptime(result["actual_start_date"], "%Y%m%d")
                actual_end = datetime.strptime(result["actual_end_date"], "%Y%m%d")
                
                # 데이터 완성도 검사
                if actual_start <= expected_start and actual_end >= expected_end:
                    result["is_complete"] = True
                    result["recommendation"] = "요청한 날짜 범위의 데이터가 모두 포함되어 있습니다."
                else:
                    result["missing_data"] = True
                    if actual_start > expected_start:
                        # 더 과거 데이터가 필요함
                        next_date = actual_start - timedelta(days=1)
                        result["next_base_date"] = next_date.strftime("%Y%m%d")
                        result["recommendation"] = f"더 과거 데이터가 필요합니다. 기준일자 {result['next_base_date']}로 추가 호출하세요."
                    else:
                        result["recommendation"] = "데이터가 충분히 수집되었지만 날짜 범위를 다시 확인하세요."
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"데이터 검증 오류: {str(e)}"}, ensure_ascii=False)


# 키움 API 툴 입력 스키마들
class TickChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    tick_scope: str = Field(description="틱범위 (1, 3, 5, 10, 30)")


class MinuteChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    minute_scope: str = Field(description="분봉범위 (1, 3, 5, 10, 15, 30, 45, 60)")


class DayChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD)")


class WeekChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD)")


class MonthChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD)")


class YearChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD)")


# 키움 API 툴 클래스들
class TickChartTool(BaseTool):
    name = "get_tick_chart"
    description = "주식 틱 차트 데이터를 조회합니다. 초 단위나 틱 단위 데이터가 필요할 때 사용하세요."
    args_schema = TickChartInput

    def _run(self, stock_code: str, tick_scope: str) -> str:
        try:
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10079(
                token=token,
                stk_cd=stock_code,
                tic_scope=tick_scope
            )
            
            if result:
                filename = f"data/{stock_code}_tick_{tick_scope}.json"
                save_chart_data_to_json(result, filename)
                return json.dumps(result, ensure_ascii=False)
            else:
                return "틱 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class MinuteChartTool(BaseTool):
    name = "get_minute_chart"
    description = "주식 분봉 차트 데이터를 조회합니다. 분 단위 데이터가 필요할 때 사용하세요."
    args_schema = MinuteChartInput

    def _run(self, stock_code: str, minute_scope: str) -> str:
        try:
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10080(
                token=token,
                stk_cd=stock_code,
                tic_scope=minute_scope
            )
            
            if result:
                filename = f"data/{stock_code}_minute_{minute_scope}.json"
                save_chart_data_to_json(result, filename)
                return json.dumps(result, ensure_ascii=False)
            else:
                return "분봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class DayChartTool(BaseTool):
    name = "get_day_chart"
    description = "주식 일봉 차트 데이터를 조회합니다. 일 단위 데이터가 필요할 때 사용하세요."
    args_schema = DayChartInput

    def _run(self, stock_code: str, base_date: str) -> str:
        try:
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10081(
                token=token,
                stk_cd=stock_code,
                base_dt=base_date
            )
            
            if result:
                filename = f"data/{stock_code}_day_{base_date}.json"
                save_chart_data_to_json(result, filename)
                return json.dumps(result, ensure_ascii=False)
            else:
                return "일봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class WeekChartTool(BaseTool):
    name = "get_week_chart"
    description = "주식 주봉 차트 데이터를 조회합니다. 주 단위 데이터가 필요할 때 사용하세요."
    args_schema = WeekChartInput

    def _run(self, stock_code: str, base_date: str) -> str:
        try:
            # LangSmith 추적용 로그
            params = {"base_date": base_date}
            log_tool_execution("주봉차트조회", stock_code, params)
            
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10082(
                token=token,
                stk_cd=stock_code,
                base_dt=base_date
            )
            
            if result:
                filename = f"data/{stock_code}_week_{base_date}.json"
                save_chart_data_to_json(result, filename)
                
                # 데이터 건수 정보 추가 (LangSmith에서 확인 가능)
                data_count = len(result.get('stk_stk_pole_chart_qry', []))
                
                if os.getenv('LANGCHAIN_API_KEY'):
                    print(f"LangSmith: 주봉 데이터 {data_count}건 조회 성공")
                
                return json.dumps(result, ensure_ascii=False)
            else:
                return "주봉 차트 데이터 조회 실패"
                
        except Exception as e:
            error_msg = f"오류 발생: {str(e)}"
            if os.getenv('LANGCHAIN_API_KEY'):
                print(f"LangSmith: 주봉차트 조회 오류 - {str(e)}")
            return error_msg


class MonthChartTool(BaseTool):
    name = "get_month_chart"
    description = "주식 월봉 차트 데이터를 조회합니다. 월 단위 데이터가 필요할 때 사용하세요."
    args_schema = MonthChartInput

    def _run(self, stock_code: str, base_date: str) -> str:
        try:
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10083(
                token=token,
                stk_cd=stock_code,
                base_dt=base_date
            )
            
            if result:
                filename = f"data/{stock_code}_month_{base_date}.json"
                save_chart_data_to_json(result, filename)
                return json.dumps(result, ensure_ascii=False)
            else:
                return "월봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class YearChartTool(BaseTool):
    name = "get_year_chart"
    description = "주식 년봉 차트 데이터를 조회합니다. 년 단위 데이터가 필요할 때 사용하세요."
    args_schema = YearChartInput

    def _run(self, stock_code: str, base_date: str) -> str:
        try:
            token_manager = get_token_manager()
            token = token_manager.get_access_token()
            
            if not token:
                return "토큰 발급 실패"
            
            result = fn_ka10094(
                token=token,
                stk_cd=stock_code,
                base_dt=base_date
            )
            
            if result:
                filename = f"data/{stock_code}_year_{base_date}.json"
                save_chart_data_to_json(result, filename)
                return json.dumps(result, ensure_ascii=False)
            else:
                return "년봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


# 모든 툴을 리스트로 정리
CHART_TOOLS = [
    ChartValidationTool(),
    TickChartTool(),
    MinuteChartTool(),
    DayChartTool(),
    WeekChartTool(),
    MonthChartTool(),
    YearChartTool()
] 