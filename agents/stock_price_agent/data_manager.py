"""
Stock Price Agent Data Manager
키움 API 응답 데이터 저장, 필터링, 관리 (새로운 로직)
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class StockDataManager:
    """키움 API 데이터 관리자 (새로운 로직)"""
    
    def __init__(self, base_path: str = None):
        """
        데이터 매니저 초기화
        
        Args:
            base_path: 데이터 저장 기본 경로
        """
        if base_path is None:
            # agents/stock_price_agent/data/ 경로 설정
            current_dir = Path(__file__).parent
            base_path = current_dir / "data"
        
        self.data_dir = Path(base_path)
        self.raw_dir = self.data_dir / "raw"          # 원본 데이터
        self.filtered_dir = self.data_dir / "filtered" # 필터링된 데이터
        
        # 차트 유형별 API 함수 매핑 초기화
        self._init_chart_configs()
        
        # 폴더 초기화
        self.initialize_directories()
    
    def _init_chart_configs(self):
        """차트 유형별 API 함수 매핑 초기화 (틱 차트 제거)"""
        self.chart_configs = {
            "minute": {
                "api_function": "ka10080",
                "data_key": "stk_min_pole_chart_qry",
                "date_field": "cntr_tm"
            },
            "day": {
                "api_function": "ka10081", 
                "data_key": "stk_dt_pole_chart_qry",
                "date_field": "dt"
            },
            "week": {
                "api_function": "ka10082",
                "data_key": "stk_stk_pole_chart_qry",
                "date_field": "dt"
            },
            "month": {
                "api_function": "ka10083",
                "data_key": "stk_mth_pole_chart_qry", 
                "date_field": "dt"
            },
            "year": {
                "api_function": "ka10094",
                "data_key": "stk_yr_pole_chart_qry",
                "date_field": "dt"
            }
        }
    
    def initialize_directories(self):
        """데이터 디렉토리 초기화"""
        try:
            # 기존 data 폴더가 있으면 삭제
            if self.data_dir.exists():
                print(f"🗑️  기존 데이터 폴더 삭제: {self.data_dir}")
                shutil.rmtree(self.data_dir, ignore_errors=True)
            
            # 새 폴더 생성
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            self.filtered_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 데이터 폴더 초기화 완료:")
            print(f"   • Raw: {self.raw_dir}")
            print(f"   • Filtered: {self.filtered_dir}")
            
        except Exception as e:
            print(f"❌ 데이터 폴더 초기화 실패: {e}")
    
    def save_raw_data(self, raw_data: Dict[str, Any], stock_code: str, chart_type: str, base_date: str = None) -> str:
        """
        원본 데이터 저장 (새로운 파일명 규칙)
        
        Args:
            raw_data: 키움 API 원본 응답
            stock_code: 종목코드
            chart_type: 차트 유형
            base_date: 기준일자 (YYYYMMDD)
            
        Returns:
            str: 저장된 파일 경로
        """
        # 새로운 파일명 규칙: {요청시간}_{api-id}_{주식종목}_{base_date}.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        api_id = self.chart_configs.get(chart_type, {}).get("api_function", "unknown")
        base_date_str = base_date if base_date else "nodate"
        
        filename = f"{timestamp}_{api_id}_{stock_code}_{base_date_str}.json"
        filepath = self.raw_dir / filename
        
        try:
            # 원본 JSON을 한 글자도 다르지 않게 그대로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 원본 데이터 저장: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 원본 데이터 저장 실패: {e}")
            return ""
    
    def _find_oldest_date_in_raw_data(self, raw_data: Dict[str, Any], chart_type: str) -> Optional[str]:
        """
        Raw 데이터에서 가장 오래된 날짜 찾기
        
        Args:
            raw_data: 키움 API 원본 응답
            chart_type: 차트 유형
            
        Returns:
            str: 가장 오래된 날짜 (YYYYMMDD) 또는 None
        """
        if chart_type not in self.chart_configs:
            return None
        
        config = self.chart_configs[chart_type]
        data_key = config["data_key"]
        date_field = config["date_field"]
        
        if data_key not in raw_data or not raw_data[data_key]:
            return None
        
        oldest_date = None
        
        for record in raw_data[data_key]:
            if isinstance(record, dict) and date_field in record:
                record_date = record[date_field]
                if record_date:
                    # 시간 정보가 있으면 제거 (YYYYMMDD만 추출)
                    if len(record_date) > 8:
                        record_date = record_date[:8]
                    
                    if oldest_date is None or record_date < oldest_date:
                        oldest_date = record_date
        
        return oldest_date
    
    def _get_chart_upgrade_suggestion(self, current_chart_type: str) -> Dict[str, str]:
        """
        차트 간격 업그레이드 제안 (틱 차트 제거)
        
        Args:
            current_chart_type: 현재 차트 유형
            
        Returns:
            Dict: 업그레이드 제안 정보
        """
        upgrade_map = {
            "minute": {"next_type": "day", "description": "분봉 → 일봉으로 차트 유형 변경"},
            "day": {"next_type": "week", "description": "일봉 → 주봉으로 차트 유형 변경"},
            "week": {"next_type": "month", "description": "주봉 → 월봉으로 차트 유형 변경"},
            "month": {"next_type": "year", "description": "월봉 → 년봉으로 차트 유형 변경"},
            "year": {"next_type": None, "description": "년봉이 최대 간격입니다. 기간을 줄이거나 분석 방법을 변경하세요."}
        }
        
        return upgrade_map.get(current_chart_type, {
            "next_type": None, 
            "description": "업그레이드 옵션이 없습니다."
        })
    
    def _filter_data_by_date_range(self, raw_data: Dict[str, Any], chart_type: str, expected_start_date: str, expected_end_date: str) -> List[Dict[str, Any]]:
        """
        날짜 범위에 맞는 데이터만 필터링하여 핵심 필드만 추출
        
        Args:
            raw_data: 키움 API 원본 응답
            chart_type: 차트 유형
            expected_start_date: 시작일 (YYYYMMDD)
            expected_end_date: 종료일 (YYYYMMDD)
            
        Returns:
            List: 필터링된 차트 데이터
        """
        if chart_type not in self.chart_configs:
            return []
        
        config = self.chart_configs[chart_type]
        data_key = config["data_key"]
        date_field = config["date_field"]
        
        if data_key not in raw_data or not raw_data[data_key]:
            return []
        
        filtered_records = []
        
        try:
            filter_start = datetime.strptime(expected_start_date, "%Y%m%d")
            filter_end = datetime.strptime(expected_end_date, "%Y%m%d")
            
            for record in raw_data[data_key]:
                if isinstance(record, dict) and date_field in record:
                    record_date_str = record[date_field]
                    if record_date_str:
                        # 시간 정보가 있으면 제거 (YYYYMMDD만 추출)
                        if len(record_date_str) > 8:
                            record_date_str = record_date_str[:8]
                        
                        try:
                            record_date = datetime.strptime(record_date_str, "%Y%m%d")
                            
                            # 날짜 범위 체크
                            if filter_start <= record_date <= filter_end:
                                # 핵심 필드만 추출
                                filtered_record = {
                                    "cur_prc": record.get("cur_prc", ""),
                                    "trde_qty": record.get("trde_qty", ""),
                                    "trde_prica": record.get("trde_prica", ""),
                                    "dt": record.get("dt", record.get("cntr_tm", "")),
                                    "open_pric": record.get("open_pric", ""),
                                    "high_pric": record.get("high_pric", ""),
                                    "low_pric": record.get("low_pric", "")
                                }
                                filtered_records.append(filtered_record)
                        except ValueError:
                            continue
            
            print(f"📅 날짜 범위 필터링 완료: {len(filtered_records)}개 레코드")
            return filtered_records
            
        except ValueError as e:
            print(f"❌ 날짜 파싱 오류: {e}")
            return []
    
    def _convert_date_format_for_chart_type(self, filtered_records: List[Dict[str, Any]], chart_type: str) -> List[Dict[str, Any]]:
        """
        차트 유형에 맞게 날짜 형식을 변환합니다
        
        Args:
            filtered_records: 필터링된 차트 데이터
            chart_type: 차트 유형
            
        Returns:
            List: 날짜 형식이 변환된 차트 데이터
        """
        if not filtered_records or chart_type not in ["minute", "day", "week", "month", "year"]:
            return filtered_records
        
        # 일봉과 분봉은 원본 유지
        if chart_type in ["day", "minute"]:
            return filtered_records
        
        converted_records = []
        
        # 주봉의 경우 월별 그룹핑 후 Week 번호 부여 (원본 순서 보존)
        if chart_type == "week":
            # 1단계: 월별로 일자 수집 및 Week 번호 매핑 테이블 생성
            monthly_day_mapping = {}
            for record in filtered_records:
                dt_str = record.get("dt", "")
                if len(dt_str) >= 8:  # YYYYMMDD 형식 확인
                    year_month = dt_str[:6]  # YYYYMM
                    day = dt_str[6:8]
                    
                    if year_month not in monthly_day_mapping:
                        monthly_day_mapping[year_month] = set()
                    monthly_day_mapping[year_month].add(day)
            
            # 2단계: 각 월의 일자들을 정렬하여 Week 번호 매핑 생성
            week_mapping = {}
            for year_month, days in monthly_day_mapping.items():
                sorted_days = sorted(list(days))  # 일자 오름차순 정렬
                for week_num, day in enumerate(sorted_days, 1):
                    week_mapping[f"{year_month}{day}"] = f"{year_month}Week{week_num}"
            
            # 3단계: 원본 순서대로 순회하면서 날짜 변환
            for record in filtered_records:
                new_record = record.copy()
                dt_str = record.get("dt", "")
                if len(dt_str) >= 8 and dt_str in week_mapping:
                    new_record["dt"] = week_mapping[dt_str]
                converted_records.append(new_record)
        
        # 월봉의 경우 YYYYMM만 남기기
        elif chart_type == "month":
            for record in filtered_records:
                new_record = record.copy()
                dt_str = record.get("dt", "")
                if len(dt_str) >= 6:  # YYYYMMDD 형식 확인
                    new_record["dt"] = dt_str[:6]  # YYYYMM
                converted_records.append(new_record)
        
        # 년봉의 경우 YYYY만 남기기
        elif chart_type == "year":
            for record in filtered_records:
                new_record = record.copy()
                dt_str = record.get("dt", "")
                if len(dt_str) >= 4:  # YYYYMMDD 형식 확인
                    new_record["dt"] = dt_str[:4]  # YYYY
                converted_records.append(new_record)
        
        print(f"📅 날짜 형식 변환 완료: {chart_type} 차트용 {len(converted_records)}개 레코드")
        return converted_records
    
    def save_filtered_data(self, filtered_records: List[Dict[str, Any]], stock_code: str, chart_type: str, base_date: str = None) -> str:
        """
        필터링된 데이터 저장
        
        Args:
            filtered_records: 필터링된 차트 데이터
            stock_code: 종목코드
            chart_type: 차트 유형
            base_date: 기준일자
            
        Returns:
            str: 저장된 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_date_str = base_date if base_date else "nodate"
        
        filename = f"{timestamp}_{chart_type}_{stock_code}_{base_date_str}_filtered.json"
        filepath = self.filtered_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_records, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 필터링된 데이터 저장: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 필터링된 데이터 저장 실패: {e}")
            return ""
    
    def process_api_response(self, raw_data: Dict[str, Any], stock_code: str, chart_type: str, base_date: str = None, expected_start_date: str = None, expected_end_date: str = None) -> Dict[str, Any]:
        """
        키움 API 응답 처리 (새로운 로직)
        
        Args:
            raw_data: 키움 API 원본 응답
            stock_code: 종목코드
            chart_type: 차트 유형
            base_date: 기준일자
            expected_start_date: 예상 시작일 (YYYYMMDD)
            expected_end_date: 예상 종료일 (YYYYMMDD)
            
        Returns:
            Dict: 처리 결과 (필터링된 데이터 또는 업그레이드 제안)
        """
        print(f"🔄 {chart_type.upper()} 차트 데이터 처리 시작: {stock_code}")
        
        # 1. 원본 데이터 저장 (새로운 파일명 규칙)
        raw_filepath = self.save_raw_data(raw_data, stock_code, chart_type, base_date)
        
        # 2. 기간 검증이 요청된 경우에만 처리
        if expected_start_date and expected_end_date:
            # 가장 오래된 날짜 찾기
            oldest_date = self._find_oldest_date_in_raw_data(raw_data, chart_type)
            
            if oldest_date:
                print(f"📅 가장 오래된 데이터: {oldest_date}, 요구한 시작일: {expected_start_date}")
                
                # 가장 오래된 데이터가 요구한 시작일보다 미래인 경우 업그레이드 제안
                if oldest_date > expected_start_date:
                    upgrade_info = self._get_chart_upgrade_suggestion(chart_type)
                    
                    result = {
                        "status": "upgrade_required",
                        "message": f"초기 기간 데이터 부족: {oldest_date} > {expected_start_date}",
                        "upgrade_suggestion": upgrade_info,
                        "raw_file": raw_filepath
                    }
                    
                    if upgrade_info["next_type"]:
                        result["suggestion"] = f"get_{upgrade_info['next_type']}_chart(stock_code='{stock_code}', base_date='{expected_end_date}')"
                    
                    print(f"❌ 업그레이드 제안: {upgrade_info['description']}")
                    return result
            
            # 3. 날짜 범위 필터링
            filtered_records = self._filter_data_by_date_range(raw_data, chart_type, expected_start_date, expected_end_date)
            
            if filtered_records:
                # 차트 유형에 맞게 날짜 형식 변환
                converted_records = self._convert_date_format_for_chart_type(filtered_records, chart_type)
                
                # 변환된 데이터 저장
                filtered_filepath = self.save_filtered_data(converted_records, stock_code, chart_type, base_date)
                
                # 추가 로직: 필터링된 레코드가 100개 초과시 업그레이드 제안
                record_count = len(converted_records)
                if record_count > 100:
                    upgrade_info = self._get_chart_upgrade_suggestion(chart_type)
                    
                    print(f"⚠️  데이터 과다 ({record_count}개 > 100개): {upgrade_info['description']}")
                    
                    result = {
                        "status": "upgrade_required",
                        "message": f"데이터 과다 ({record_count}개 레코드 > 100개 권장): 더 큰 차트 간격 사용 권장",
                        "upgrade_suggestion": upgrade_info,
                        "data_count": record_count,
                        "raw_file": raw_filepath,
                        "filtered_file": filtered_filepath
                    }
                    
                    if upgrade_info["next_type"]:
                        result["suggestion"] = f"get_{upgrade_info['next_type']}_chart(stock_code='{stock_code}', base_date='{expected_end_date}', expected_start_date='{expected_start_date}', expected_end_date='{expected_end_date}')"
                    
                    return result
                
                # 100개 이하인 경우 정상 반환
                return {
                    "status": "success",
                    "message": f"데이터 필터링 완료: {record_count}개 레코드",
                    "data": converted_records,
                    "raw_file": raw_filepath,
                    "filtered_file": filtered_filepath
                }
            else:
                return {
                    "status": "no_data",
                    "message": "지정된 날짜 범위에 데이터가 없습니다.",
                    "raw_file": raw_filepath
                }
        
        # 4. 기간 검증이 요청되지 않은 경우 원본 데이터 그대로 반환
        return {
            "status": "raw_data",
            "message": "원본 데이터 저장 완료",
            "data": raw_data,
            "raw_file": raw_filepath
        }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """현재 저장된 데이터 요약 정보 반환"""
        summary = {
            "raw_files": len(list(self.raw_dir.glob("*.json"))) if self.raw_dir.exists() else 0,
            "filtered_files": len(list(self.filtered_dir.glob("*.json"))) if self.filtered_dir.exists() else 0,
            "total_size_mb": 0,
            "chart_types_supported": list(self.chart_configs.keys())
        }
        
        # 총 크기 계산
        total_size = 0
        for dir_path in [self.raw_dir, self.filtered_dir]:
            if dir_path.exists():
                for file_path in dir_path.rglob("*.json"):
                    total_size += file_path.stat().st_size
        
        summary["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return summary


# 전역 데이터 매니저 인스턴스
_data_manager = None

def get_data_manager() -> StockDataManager:
    """전역 데이터 매니저 인스턴스 반환"""
    global _data_manager
    if _data_manager is None:
        _data_manager = StockDataManager()
    return _data_manager


def process_api_response_for_tools(raw_data: Dict[str, Any], stock_code: str, chart_type: str, base_date: str = None, expected_start_date: str = None, expected_end_date: str = None) -> str:
    """
    키움 API 응답을 처리하고 결과를 반환 (LangChain 도구 전용)
    
    Args:
        raw_data: 키움 API 원본 응답
        stock_code: 종목코드
        chart_type: 차트 유형
        base_date: 기준일자
        expected_start_date: 예상 시작일 (YYYYMMDD)
        expected_end_date: 예상 종료일 (YYYYMMDD)
        
    Returns:
        str: 처리 결과 JSON 문자열
    """
    try:
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