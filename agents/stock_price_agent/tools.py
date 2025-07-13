"""
Stock Price Agent 툴 구현
키움 API 함수들을 LangChain 툴로 래핑 (틱 차트 제거)
"""
from typing import Dict, Optional, List, Tuple, Any
from langchain.tools import BaseTool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 자체 구현한 키움 API 모듈 import
from .kiwoom_api import (
    fn_ka10080, fn_ka10081, 
    fn_ka10082, fn_ka10083, fn_ka10094,
    get_token_manager, get_today_date
)
'''from .prompt import QUERY_ANALYSIS_PROMPT'''

# 환경변수 로드
load_dotenv("secrets/.env")


def log_tool_execution(tool_name: str, stock_code: str, params: Dict) -> str:
    """툴 실행 로그를 생성합니다 (LangSmith 추적용)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {tool_name} 실행: 종목={stock_code}, 파라미터={params}"
    
    # LangSmith가 활성화된 경우에만 상세 로그
    if os.getenv('LANGSMITH_API_KEY'):
        print(f"LangSmith 추적: {log_msg}")
    
    return log_msg


def _process_api_response(raw_data: Dict, stock_code: str, chart_type: str, base_date: str = None, expected_start_date: str = None, expected_end_date: str = None) -> str:
    """
    키움 API 응답을 처리하고 결과를 반환 (새로운 로직)
    
    Args:
        raw_data: 키움 API 원본 응답
        stock_code: 종목코드  
        chart_type: 차트 유형
        base_date: 기준일자
        expected_start_date: 예상 시작일 (YYYYMMDD, 선택적)
        expected_end_date: 예상 종료일 (YYYYMMDD, 선택적)
        
    Returns:
        str: 처리 결과 JSON 문자열
    """
    try:
        # 데이터 매니저 import (순환 import 방지)
        from .data_manager import get_data_manager
        
        # 기간 정보 로그 출력
        if expected_start_date and expected_end_date:
            print(f"🔍 기간 검증 활성화: {expected_start_date} ~ {expected_end_date}")
        else:
            print(f"ℹ️  기간 검증 생략 (기간 정보 없음)")
        
        # 데이터 처리 (새로운 로직)
        data_manager = get_data_manager()
        result = data_manager.process_api_response(
            raw_data, stock_code, chart_type, base_date, expected_start_date, expected_end_date
        )
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ 데이터 처리 오류: {e}")
        # 오류 시 원본 데이터 반환
        return json.dumps({
            "status": "error",
            "message": f"데이터 처리 오류: {str(e)}",
            "data": raw_data
        }, ensure_ascii=False)

'''
class QueryAnalysisInput(BaseModel):
    user_query: str = Field(description="분석할 사용자 질문")


class QueryAnalysisTool(BaseTool):
    name: str = "analyze_query"
    description: str = "사용자 쿼리에서 종목 티커와 날짜 범위를 정확하게 분석합니다. 내부에서 모든 상대적 날짜(오늘, 어제, 올해, 작년 등)를 Python으로 정확히 계산합니다."
    args_schema: type = QueryAnalysisInput
    
    def _run(self, user_query: str) -> str:
        try:
            # Python에서 정확한 현재 날짜 기반으로 모든 상대적 날짜 계산
            actual_today = datetime.now()
            
            # 모든 상대적 날짜들을 Python에서 정확히 계산
            today_date = actual_today.strftime('%Y%m%d')
            yesterday_date = (actual_today - timedelta(days=1)).strftime('%Y%m%d')
            tomorrow_date = (actual_today + timedelta(days=1)).strftime('%Y%m%d')
            
            # 이번달 계산
            this_month_start = actual_today.replace(day=1).strftime('%Y%m%d')
            if actual_today.month == 12:
                next_month = actual_today.replace(year=actual_today.year+1, month=1, day=1)
            else:
                next_month = actual_today.replace(month=actual_today.month+1, day=1)
            this_month_end = (next_month - timedelta(days=1)).strftime('%Y%m%d')
            
            # 지난달 계산
            if actual_today.month == 1:
                last_month_start = actual_today.replace(year=actual_today.year-1, month=12, day=1).strftime('%Y%m%d')
                last_month_end = actual_today.replace(day=1) - timedelta(days=1)
                last_month_end = last_month_end.strftime('%Y%m%d')
            else:
                last_month_start = actual_today.replace(month=actual_today.month-1, day=1).strftime('%Y%m%d')
                last_month_end = actual_today.replace(day=1) - timedelta(days=1)
                last_month_end = last_month_end.strftime('%Y%m%d')
            
            # 다음달 계산
            next_month_start = next_month.strftime('%Y%m%d')
            if next_month.month == 12:
                next_next_month = next_month.replace(year=next_month.year+1, month=1, day=1)
            else:
                next_next_month = next_month.replace(month=next_month.month+1, day=1)
            next_month_end = (next_next_month - timedelta(days=1)).strftime('%Y%m%d')
            
            # 올해/작년 계산
            this_year_start = actual_today.replace(month=1, day=1).strftime('%Y%m%d')
            this_year_end = actual_today.replace(month=12, day=31).strftime('%Y%m%d')
            last_year_start = actual_today.replace(year=actual_today.year-1, month=1, day=1).strftime('%Y%m%d')
            last_year_end = actual_today.replace(year=actual_today.year-1, month=12, day=31).strftime('%Y%m%d')
            
            print(f"🔍 쿼리 분석 시작")
            print(f"   🔥 Python 계산 기준:")
            print(f"      오늘: {today_date}")
            print(f"      어제: {yesterday_date}, 내일: {tomorrow_date}")
            print(f"      이번달: {this_month_start}~{this_month_end}")
            print(f"      지난달: {last_month_start}~{last_month_end}")
            print(f"      다음달: {next_month_start}~{next_month_end}")
            print(f"      올해: {this_year_start}~{this_year_end}")
            print(f"      작년: {last_year_start}~{last_year_end}")
            
            # LLM 생성 (매번 새로 생성하여 Pydantic 모델 검증 문제 회피)
            llm = ChatOpenAI(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                temperature=0,  # 정확한 분석을 위해 temperature 0
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
            
            # 날짜 계산 (프롬프트에 전달할 추가 정보)
            current_year = actual_today.year
            last_year = current_year - 1
            
            # prompt.py의 QUERY_ANALYSIS_PROMPT 사용 (모든 날짜 정보 전달)
            analysis_prompt = QUERY_ANALYSIS_PROMPT.format(
                today_date=today_date,
                yesterday_date=yesterday_date,
                tomorrow_date=tomorrow_date,
                this_month_start=this_month_start,
                this_month_end=this_month_end,
                last_month_start=last_month_start,
                last_month_end=last_month_end,
                next_month_start=next_month_start,
                next_month_end=next_month_end,
                this_year_start=this_year_start,
                this_year_end=this_year_end,
                last_year_start=last_year_start,
                last_year_end=last_year_end,
                current_year=current_year,
                last_year=last_year,
                user_query=user_query
            )
            
            print(f"🔍 쿼리 분석 중 (기준일: {today_date}, 현재 연도: {current_year})")
            
            # LLM으로 쿼리 분석 실행
            messages = [HumanMessage(content=analysis_prompt)]
            response = llm.invoke(messages)
            
            # 응답에서 JSON 추출
            response_content = response.content.strip()
            
            # JSON 코드블록 제거 (```json ... ``` 형태인 경우)
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "").replace("```", "").strip()
            elif response_content.startswith("```"):
                response_content = response_content.replace("```", "").strip()
            
            # JSON 유효성 검증
            try:
                parsed_result = json.loads(response_content)
                stock_count = parsed_result.get('total_stocks', 0)
                summary = parsed_result.get('analysis_summary', '분석 완료')
                print(f"✅ 쿼리 분석 완료: {stock_count}개 종목 발견")
                print(f"📋 분석 요약: {summary}")
                return response_content
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {e}")
                print(f"📄 원본 응답: {response_content[:200]}...")
                # 기본 응답 반환
                return json.dumps({
                    "analysis_result": {},
                    "total_stocks": 0,
                    "analysis_summary": f"쿼리 분석 오류: JSON 파싱 실패 - {str(e)}"
                }, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ 쿼리 분석 툴 오류: {e}")
            return json.dumps({
                "analysis_result": {},
                "total_stocks": 0,
                "analysis_summary": f"분석 도구 오류: {str(e)}"
            }, ensure_ascii=False)
'''

class MinuteChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    minute_scope: str = Field(description="분봉범위 (1, 3, 5, 10, 15, 30, 45, 60)")
    expected_start_date: Optional[str] = Field(None, description="검증용 시작일 (YYYYMMDD, 선택적)")
    expected_end_date: Optional[str] = Field(None, description="검증용 종료일 (YYYYMMDD, 선택적)")


class DayChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD) - 원하는 기간의 종료일")
    expected_start_date: Optional[str] = Field(None, description="검증용 시작일 (YYYYMMDD, 선택적)")
    expected_end_date: Optional[str] = Field(None, description="검증용 종료일 (YYYYMMDD, 선택적)")


class WeekChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD) - 원하는 기간의 종료일")
    expected_start_date: Optional[str] = Field(None, description="검증용 시작일 (YYYYMMDD, 선택적)")
    expected_end_date: Optional[str] = Field(None, description="검증용 종료일 (YYYYMMDD, 선택적)")


class MonthChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD) - 원하는 기간의 종료일")
    expected_start_date: Optional[str] = Field(None, description="검증용 시작일 (YYYYMMDD, 선택적)")
    expected_end_date: Optional[str] = Field(None, description="검증용 종료일 (YYYYMMDD, 선택적)")


class YearChartInput(BaseModel):
    stock_code: str = Field(description="6자리 종목코드 (예: 005930)")
    base_date: str = Field(description="기준일자 (YYYYMMDD) - 원하는 기간의 종료일")
    expected_start_date: Optional[str] = Field(None, description="검증용 시작일 (YYYYMMDD, 선택적)")
    expected_end_date: Optional[str] = Field(None, description="검증용 종료일 (YYYYMMDD, 선택적)")


class MinuteChartTool(BaseTool):
    name: str = "get_minute_chart"
    description: str = "주식 분봉차트 조회 (1, 3, 5, 10, 15, 30, 45, 60분 범위). 단기 트레이딩 및 일중 패턴 분석용으로 1일~1주일 기간에 적합."
    args_schema: type = MinuteChartInput

    def _run(self, stock_code: str, minute_scope: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
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
                return _process_api_response(result, stock_code, "minute", None, expected_start_date, expected_end_date)
            else:
                return "분봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class DayChartTool(BaseTool):
    name: str = "get_day_chart"
    description: str = "주식 일봉차트 조회. 중단기 분석의 표준으로 1주일~1년 기간의 일반적인 기술적 분석에 가장 적합. 기준일자 역순으로 과거 데이터 조회."
    args_schema: type = DayChartInput

    def _run(self, stock_code: str, base_date: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
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
                return _process_api_response(result, stock_code, "day", base_date, expected_start_date, expected_end_date)
            else:
                return "일봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class WeekChartTool(BaseTool):
    name: str = "get_week_chart"
    description: str = "주식 주봉차트 조회. 중장기 트렌드 및 패턴 분석용으로 1개월~5년 기간의 거시적 흐름 파악에 적합. 노이즈 제거된 안정적 패턴 확인 가능."
    args_schema: type = WeekChartInput

    def _run(self, stock_code: str, base_date: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
        try:
            # LangSmith 추적용 로그
            params = {"base_date": base_date, "period": f"{expected_start_date}~{expected_end_date}" if expected_start_date else "unknown"}
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
                filtered_result = _process_api_response(result, stock_code, "week", base_date, expected_start_date, expected_end_date)
                
                # 데이터 건수 정보 추가 (LangSmith에서 확인 가능)
                if os.getenv('LANGSMITH_API_KEY'):
                    try:
                        data = json.loads(filtered_result)
                        if data.get("status") == "success":
                            data_count = len(data.get('data', []))
                            period_info = f" (기간: {expected_start_date}~{expected_end_date})" if expected_start_date else ""
                            print(f"LangSmith: 주봉 데이터 {data_count}건 조회 성공{period_info}")
                    except:
                        pass
                
                return filtered_result
            else:
                return "주봉 차트 데이터 조회 실패"
                
        except Exception as e:
            error_msg = f"오류 발생: {str(e)}"
            if os.getenv('LANGSMITH_API_KEY'):
                print(f"LangSmith: 주봉차트 조회 오류 - {str(e)}")
            return error_msg


class MonthChartTool(BaseTool):
    name: str = "get_month_chart"
    description: str = "주식 월봉차트 조회. 장기 트렌드 및 펀더멘털 분석용으로 6개월~10년 기간의 거시경제 영향과 기업 실적 반영 패턴 확인에 적합."
    args_schema: type = MonthChartInput

    def _run(self, stock_code: str, base_date: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
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
                return _process_api_response(result, stock_code, "month", base_date, expected_start_date, expected_end_date)
            else:
                return "월봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


class YearChartTool(BaseTool):
    name: str = "get_year_chart"
    description: str = "주식 년봉차트 조회. 초장기 히스토리 분석용으로 5년 이상의 역사적 패턴, 경기 사이클, 구조적 변화 분석에 적합. 장기 투자 관점에서 사용."
    args_schema: type = YearChartInput

    def _run(self, stock_code: str, base_date: str, expected_start_date: str = None, expected_end_date: str = None) -> str:
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
                return _process_api_response(result, stock_code, "year", base_date, expected_start_date, expected_end_date)
            else:
                return "년봉 차트 데이터 조회 실패"
                
        except Exception as e:
            return f"오류 발생: {str(e)}"


def get_stock_price_tools() -> List[BaseTool]:
    """
    Stock Price Agent에서 사용할 툴 리스트를 반환합니다. (틱 차트 제거)
    쿼리 분석 툴이 추가되어 더 정확한 종목과 날짜 범위 분석이 가능합니다.
    
    Returns:
        List[BaseTool]: 쿼리 분석 + 키움증권 API 툴들 (틱 차트 제외)
    """
    return [
        # QueryAnalysisTool(),      # 쿼리 분석 툴 (날짜 계산 포함)
        MinuteChartTool(),
        DayChartTool(),
        WeekChartTool(),
        MonthChartTool(),
        YearChartTool()
    ] 