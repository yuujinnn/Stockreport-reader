"""
Stock Price Agent Data Manager
키움 API 응답 데이터 저장, 필터링, 관리 (legacy 코드 기반 실제 응답 구조)
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 날짜 함수 import
from .kiwoom_api import get_today_date


class StockDataManager:
    """키움 API 데이터 관리자 (legacy 코드 기반 실제 응답 구조)"""
    
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
        
        # 차트 유형별 설정 초기화 (legacy 코드 기반)
        self._init_chart_configs()
        
        # 폴더 초기화
        self.initialize_directories()
    
    def _init_chart_configs(self):
        """차트 유형별 필터링 설정 초기화 (legacy 코드 실제 응답 구조 기반)"""
        
        # 차트 유형별 특화 설정 (legacy kiwoom.py 응답 구조 참고)
        self.chart_configs = {
            "tick": {
                "api_function": "ka10079",
                "data_keys": ["stk_tic_chart_qry"],  # 틱차트 전용 키
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "cntr_tm",           # 체결시간
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "cntr_tm"  # 체결시간
            },
            "minute": {
                "api_function": "ka10080",
                "data_keys": ["stk_min_pole_chart_qry"],  # 분봉차트 전용 키
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "cntr_tm",           # 체결시간
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "cntr_tm"  # 체결시간
            },
            "day": {
                "api_function": "ka10081",
                "data_keys": ["stk_dt_pole_chart_qry"],  # 일봉차트 전용 키
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "trde_prica",        # 거래대금
                    "dt",                # 일자
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "dt"  # 일자
            },
            "week": {
                "api_function": "ka10082",
                "data_keys": ["stk_stk_pole_chart_qry"],  # 주봉차트 전용 키 (stk_stk_pole)
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "trde_prica",        # 거래대금
                    "dt",                # 일자
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "dt"  # 일자
            },
            "month": {
                "api_function": "ka10083",
                "data_keys": ["stk_mth_pole_chart_qry"],  # 월봉차트 전용 키
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "trde_prica",        # 거래대금
                    "dt",                # 일자
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "dt"  # 일자
            },
            "year": {
                "api_function": "ka10094",
                "data_keys": ["stk_yr_pole_chart_qry"],  # 년봉차트 전용 키
                "essential_fields": {
                    "cur_prc",           # 현재가
                    "trde_qty",          # 거래량
                    "trde_prica",        # 거래대금
                    "dt",                # 일자
                    "open_pric",         # 시가
                    "high_pric",         # 고가
                    "low_pric",          # 저가
                },
                "date_field": "dt"  # 일자
            }
        }
    
    def initialize_directories(self):
        """데이터 디렉토리 초기화 (Windows 권한 문제 해결하면서 기존 데이터 삭제)"""
        try:
            # 기존 data 폴더가 있으면 강력하게 삭제
            if self.data_dir.exists():
                print(f"🗑️  기존 데이터 폴더 삭제 시도: {self.data_dir}")
                
                # Windows에서 안전한 삭제 방법
                import stat
                
                # 모든 파일의 읽기 전용 속성 제거
                for root, dirs, files in os.walk(self.data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, stat.S_IWRITE)
                        except:
                            pass
                
                # 폴더 삭제 시도
                shutil.rmtree(self.data_dir, ignore_errors=True)
                
                # 삭제 확인
                if self.data_dir.exists():
                    print(f"⚠️  일부 파일이 남아있습니다. 수동으로 정리합니다.")
                    # 개별 파일 삭제 시도
                    for root, dirs, files in os.walk(self.data_dir, topdown=False):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except:
                                pass
                        for dir in dirs:
                            try:
                                os.rmdir(os.path.join(root, dir))
                            except:
                                pass
                    # 최종 폴더 삭제 시도
                    try:
                        os.rmdir(self.data_dir)
                    except:
                        print(f"⚠️  폴더 완전 삭제 실패. 기존 파일들과 함께 진행합니다.")
                else:
                    print(f"✅ 기존 데이터 폴더 삭제 완료")
            
            # 새 폴더 생성
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            self.filtered_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 데이터 폴더 초기화 완료:")
            print(f"   • Raw: {self.raw_dir}")
            print(f"   • Filtered: {self.filtered_dir}")
            
        except Exception as e:
            print(f"❌ 데이터 폴더 초기화 실패: {e}")
            print(f"💡 해결 방법: 관리자 권한으로 실행하거나 '{self.data_dir}' 폴더를 수동으로 삭제해주세요.")
    
    def save_raw_data(self, data: Dict[str, Any], filename: str) -> str:
        """
        원본 데이터 저장
        
        Args:
            data: 키움 API 원본 응답
            filename: 저장할 파일명 (확장자 제외)
            
        Returns:
            str: 저장된 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.raw_dir / f"{filename}_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 원본 데이터 저장: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 원본 데이터 저장 실패: {e}")
            return ""
    
    def _find_chart_data_key(self, raw_data: Dict[str, Any], chart_type: str) -> Optional[str]:
        """
        차트 유형에 따라 적절한 데이터 키를 찾습니다 (legacy 응답 구조 기반)
        
        Args:
            raw_data: 원본 API 응답
            chart_type: 차트 유형
            
        Returns:
            str: 찾은 데이터 키 또는 None
        """
        if chart_type not in self.chart_configs:
            print(f"⚠️  알 수 없는 차트 유형: {chart_type}")
            return None
        
        config = self.chart_configs[chart_type]
        data_keys = config["data_keys"]
        
        # 우선순위대로 키 찾기 (legacy 구조 기반)
        for key in data_keys:
            if key in raw_data and isinstance(raw_data[key], list) and raw_data[key]:
                print(f"✅ 차트 데이터 키 발견: {key} ({len(raw_data[key])}개 레코드)")
                return key
        
        # 백업: 모든 키를 확인하여 리스트 형태의 데이터 찾기
        for key, value in raw_data.items():
            if isinstance(value, list) and value:
                # 첫 번째 요소가 딕셔너리이고 차트 데이터 같은 구조인지 확인
                if isinstance(value[0], dict):
                    sample_keys = set(value[0].keys())
                    # 필수 필드가 포함된 것으로 보이는지 확인
                    essential_fields = config["essential_fields"]
                    if any(field in sample_keys for field in essential_fields):
                        print(f"🔍 백업 키 발견: {key} ({len(value)}개 레코드)")
                        return key
        
        print(f"❌ {chart_type} 차트용 데이터 키를 찾을 수 없음")
        return None
    
    def _extract_essential_fields(self, record: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """
        차트 유형에 따라 필수 필드를 추출합니다 (legacy 구조 기반)
        
        Args:
            record: 개별 차트 레코드
            chart_type: 차트 유형
            
        Returns:
            Dict: 추출된 필수 필드들
        """
        if chart_type not in self.chart_configs:
            return {}
        
        config = self.chart_configs[chart_type]
        essential_fields = config["essential_fields"]
        
        filtered_record = {}
        
        # 필수 필드 추출
        for field in essential_fields:
            if field in record:
                filtered_record[field] = record[field]
        
        # 날짜 필드 보장
        date_field = config["date_field"]
        if date_field in record:
            if date_field not in filtered_record:  # 중복 방지
                filtered_record[date_field] = record[date_field]
        else:
            print(f"⚠️  날짜 필드({date_field})를 찾을 수 없습니다: {list(record.keys())[:5]}...")
        
        return filtered_record
    
    def filter_chart_data(self, raw_data: Dict[str, Any], chart_type: str = "day", expected_start_date: str = None, expected_end_date: str = None) -> Dict[str, Any]:
        """
        차트 유형에 따라 키움 API 차트 데이터에서 필요한 필드만 추출 (legacy 구조 기반)
        날짜 범위가 제공된 경우 해당 기간의 데이터만 필터링하여 토큰 절약
        
        Args:
            raw_data: 키움 API 원본 응답
            chart_type: 차트 유형 (tick, minute, day, week, month, year)
            expected_start_date: 원하는 시작일 (YYYYMMDD, 선택적)
            expected_end_date: 원하는 종료일 (YYYYMMDD, 선택적)
            
        Returns:
            Dict: 필터링된 데이터 (날짜 범위 적용)
        """
        filtered_data = {
            "metadata": {
                "filtered_at": datetime.now().isoformat(),
                "chart_type": chart_type,
                "api_function": self.chart_configs.get(chart_type, {}).get("api_function", "unknown"),
                "original_size": len(str(raw_data)),
                "api_response_code": raw_data.get("rt_cd", "Unknown"),
                "stock_code": raw_data.get("stk_cd", "Unknown"),
                "date_range_filter": f"{expected_start_date}~{expected_end_date}" if expected_start_date and expected_end_date else "none"
            }
        }
        
        # 차트 데이터 키 찾기
        chart_data_key = self._find_chart_data_key(raw_data, chart_type)
        
        if chart_data_key and raw_data[chart_data_key]:
            filtered_charts = []
            raw_charts = raw_data[chart_data_key]
            
            print(f"🔄 {chart_type} 차트 데이터 필터링 시작 ({len(raw_charts)}개 레코드)")
            
            # 날짜 범위 필터링이 요청된 경우
            date_filter_active = expected_start_date and expected_end_date
            if date_filter_active:
                try:
                    filter_start = datetime.strptime(expected_start_date, "%Y%m%d")
                    filter_end = datetime.strptime(expected_end_date, "%Y%m%d")
                    print(f"📅 날짜 범위 필터링 활성화: {expected_start_date} ~ {expected_end_date}")
                except ValueError as e:
                    print(f"❌ 날짜 파싱 오류: {e}, 날짜 필터링 비활성화")
                    date_filter_active = False
            
            original_count = len(raw_charts)
            filtered_count = 0
            date_field = self.chart_configs.get(chart_type, {}).get("date_field", "dt")
            
            for i, record in enumerate(raw_charts):
                if isinstance(record, dict):
                    # 차트 유형별 필수 필드 추출
                    filtered_record = self._extract_essential_fields(record, chart_type)
                    
                    # 빈 레코드가 아니면 날짜 필터링 적용
                    if filtered_record:
                        # 날짜 범위 필터링 (활성화된 경우)
                        if date_filter_active:
                            record_date_str = record.get(date_field, "")
                            if record_date_str:
                                try:
                                    # 날짜 형식 처리 (시간 정보가 있을 수 있음)
                                    if len(record_date_str) > 8:
                                        record_date = datetime.strptime(record_date_str[:8], "%Y%m%d")
                                    else:
                                        record_date = datetime.strptime(record_date_str, "%Y%m%d")
                                    
                                    # 날짜 범위 체크
                                    if filter_start <= record_date <= filter_end:
                                        filtered_charts.append(filtered_record)
                                        filtered_count += 1
                                    # 범위 밖 데이터는 제외 (토큰 절약)
                                except ValueError:
                                    # 날짜 파싱 실패한 레코드는 포함 (안전장치)
                                    filtered_charts.append(filtered_record)
                                    filtered_count += 1
                            else:
                                # 날짜 정보 없는 레코드는 포함 (안전장치)
                                filtered_charts.append(filtered_record)
                                filtered_count += 1
                        else:
                            # 날짜 필터링 비활성화된 경우 모든 데이터 포함
                            filtered_charts.append(filtered_record)
                            filtered_count += 1
                    elif i < 3:  # 처음 몇 개만 디버그 출력
                        print(f"⚠️  빈 레코드 발견 (index {i}): {list(record.keys())[:5]}...")
            
            filtered_data["chart_data"] = filtered_charts
            filtered_data["data_count"] = len(filtered_charts)
            
            # 토큰 절약 통계
            original_size = len(json.dumps(raw_data, ensure_ascii=False))
            filtered_size = len(json.dumps(filtered_data, ensure_ascii=False))
            reduction_percent = int((1 - filtered_size / original_size) * 100) if original_size > 0 else 0
            
            # 날짜 필터링 효과 로그
            if date_filter_active and original_count > filtered_count:
                date_reduction = int((1 - filtered_count / original_count) * 100)
                print(f"📅 날짜 필터링 효과: {original_count} → {filtered_count}개 레코드 ({date_reduction}% 감소)")
            
            print(f"✅ 필터링 완료: {original_count} → {filtered_count}개 레코드")
            print(f"📊 토큰 절약: {reduction_percent}% (원본 {original_size} → 필터링 {filtered_size} bytes)")
            
        else:
            filtered_data["chart_data"] = []
            filtered_data["data_count"] = 0
            
            # 디버그: 사용 가능한 키들 출력
            available_keys = [k for k, v in raw_data.items() if isinstance(v, list)]
            print(f"⚠️  차트 데이터 없음. 사용 가능한 리스트 키들: {available_keys}")
        
        return filtered_data
    
    def save_filtered_data(self, filtered_data: Dict[str, Any], filename: str) -> str:
        """
        필터링된 데이터 저장
        
        Args:
            filtered_data: 필터링된 차트 데이터
            filename: 저장할 파일명 (확장자 제외)
            
        Returns:
            str: 저장된 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_type = filtered_data.get("metadata", {}).get("chart_type", "unknown")
        filepath = self.filtered_dir / f"{filename}_{chart_type}_filtered_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 필터링된 데이터 저장: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 필터링된 데이터 저장 실패: {e}")
            return ""
    
    def _get_chart_upgrade_suggestion(self, current_chart_type: str, current_params: str = None) -> Dict[str, str]:
        """
        현재 차트 유형에서 더 넓은 간격의 차트 유형으로 업그레이드 제안
        
        Args:
            current_chart_type: 현재 차트 유형
            current_params: 현재 파라미터 (틱/분봉의 경우)
            
        Returns:
            Dict: 업그레이드 제안 정보
        """
        upgrade_map = {
            "tick": {
                "1": {"next_type": "tick", "next_param": "3", "description": "1틱 → 3틱으로 데이터 밀도 감소"},
                "3": {"next_type": "tick", "next_param": "5", "description": "3틱 → 5틱으로 데이터 밀도 감소"},
                "5": {"next_type": "tick", "next_param": "10", "description": "5틱 → 10틱으로 데이터 밀도 감소"},
                "10": {"next_type": "tick", "next_param": "30", "description": "10틱 → 30틱으로 데이터 밀도 감소"},
                "30": {"next_type": "minute", "next_param": "1", "description": "30틱 → 1분봉으로 차트 유형 변경"}
            },
            "minute": {
                "1": {"next_type": "minute", "next_param": "3", "description": "1분봉 → 3분봉으로 데이터 밀도 감소"},
                "3": {"next_type": "minute", "next_param": "5", "description": "3분봉 → 5분봉으로 데이터 밀도 감소"},
                "5": {"next_type": "minute", "next_param": "15", "description": "5분봉 → 15분봉으로 데이터 밀도 감소"},
                "15": {"next_type": "minute", "next_param": "30", "description": "15분봉 → 30분봉으로 데이터 밀도 감소"},
                "30": {"next_type": "minute", "next_param": "60", "description": "30분봉 → 60분봉으로 데이터 밀도 감소"},
                "60": {"next_type": "day", "next_param": None, "description": "60분봉 → 일봉으로 차트 유형 변경"}
            },
            "day": {"next_type": "week", "next_param": None, "description": "일봉 → 주봉으로 차트 유형 변경"},
            "week": {"next_type": "month", "next_param": None, "description": "주봉 → 월봉으로 차트 유형 변경"},
            "month": {"next_type": "year", "next_param": None, "description": "월봉 → 년봉으로 차트 유형 변경"},
            "year": {"next_type": None, "next_param": None, "description": "년봉이 최대 간격입니다. 기간을 줄이거나 분석 방법을 변경하세요."}
        }
        
        if current_chart_type in upgrade_map:
            if isinstance(upgrade_map[current_chart_type], dict) and current_params:
                # 틱/분봉의 경우 파라미터별 업그레이드
                return upgrade_map[current_chart_type].get(current_params, 
                    {"next_type": None, "next_param": None, "description": f"알 수 없는 {current_chart_type} 파라미터: {current_params}"})
            else:
                # 일/주/월/년봉의 경우 직접 업그레이드
                return upgrade_map[current_chart_type]
        
        return {"next_type": None, "next_param": None, "description": "업그레이드 옵션이 없습니다."}
    
    def _validate_raw_data_coverage(self, raw_data: Dict[str, Any], chart_type: str, chart_params: str = None, expected_start_date: str = None, expected_end_date: str = None) -> Dict[str, Any]:
        """
        raw 데이터에서 기간 커버리지를 먼저 검증 (필터링 전)
        
        키움 API는 base_date 기준으로 과거 300개 레코드를 가져옵니다.
        업그레이드가 필요한 경우: 받아온 raw 데이터의 가장 과거 날짜가 
        요구한 시작날짜보다 미래인 경우 (= 초기 기간 데이터 부족)
        
        Args:
            raw_data: 키움 API 원본 응답
            chart_type: 차트 유형
            chart_params: 차트 파라미터 (틱/분봉: scope, 일/주/월/년봉: None)
            expected_start_date: 요구한 시작일 (YYYYMMDD)
            expected_end_date: 요구한 종료일 (YYYYMMDD)
            
        Returns:
            Dict: 검증 결과 및 업그레이드 제안 포함
        """
        validation_result = {
            "data_validation": {
                "is_complete": True,
                "data_coverage": "complete",
                "recommendation": "✅ 데이터가 정상적으로 수집되었습니다.",
                "chart_upgrade_suggestion": None
            }
        }
        
        # 기간 검증이 요청되지 않은 경우 성공으로 처리
        if not expected_start_date or not expected_end_date:
            return validation_result
        
        # 차트 데이터 키 찾기
        chart_data_key = self._find_chart_data_key(raw_data, chart_type)
        
        if not chart_data_key or not raw_data[chart_data_key]:
            validation_result["data_validation"]["is_complete"] = False
            validation_result["data_validation"]["data_coverage"] = "no_data"
            validation_result["data_validation"]["recommendation"] = "❌ 데이터가 없습니다. API 호출 파라미터를 확인하거나 다른 종목을 시도하세요."
            return validation_result
        
        raw_charts = raw_data[chart_data_key]
        print(f"🔍 Raw 데이터 기간 검증 시작 ({len(raw_charts)}개 레코드)")
        
        try:
            # raw 데이터에서 가장 오래된 날짜 찾기
            date_fields = ['dt', 'cntr_tm']  # 차트별 날짜 필드
            oldest_date = None
            
            for record in raw_charts:
                if isinstance(record, dict):
                    for date_field in date_fields:
                        if date_field in record and record[date_field]:
                            record_date = record[date_field]
                            # 시간 정보가 있으면 제거 (YYYYMMDD만 추출)
                            if len(record_date) > 8:
                                record_date = record_date[:8]
                            
                            if oldest_date is None or record_date < oldest_date:
                                oldest_date = record_date
                            break
            
            if oldest_date:
                print(f"📅 Raw 데이터 가장 오래된 날짜: {oldest_date}, 요구한 시작일: {expected_start_date}")
                
                # 가장 오래된 데이터가 요구한 시작일보다 미래인지 확인
                if oldest_date > expected_start_date:
                    validation_result["data_validation"]["is_complete"] = False
                    validation_result["data_validation"]["data_coverage"] = "period_insufficient"
                    
                    # 업그레이드 제안
                    upgrade_info = self._get_chart_upgrade_suggestion(chart_type, chart_params)
                    validation_result["data_validation"]["chart_upgrade_suggestion"] = upgrade_info
                    
                    stock_code = raw_data.get("stk_cd", "UNKNOWN")
                    
                    if upgrade_info["next_type"]:
                        if upgrade_info["next_param"]:
                            suggestion = f"get_{upgrade_info['next_type']}_chart(stock_code='{stock_code}', {upgrade_info['next_type']}_scope='{upgrade_info['next_param']}')"
                        else:
                            suggestion = f"get_{upgrade_info['next_type']}_chart(stock_code='{stock_code}', base_date='{expected_end_date}')"
                        
                        validation_result["data_validation"]["recommendation"] = (
                            f"⚠️ 초기 기간 데이터가 부족합니다.\n"
                            f"요구한 시작일: {expected_start_date}, 실제 가장 오래된 데이터: {oldest_date}\n"
                            f"💡 제안: {upgrade_info['description']}\n"
                            f"🔧 호출 예시: {suggestion}"
                        )
                    else:
                        validation_result["data_validation"]["recommendation"] = (
                            f"⚠️ 초기 기간 데이터가 부족합니다. {upgrade_info['description']}\n"
                            f"기간을 줄이거나 분석 방법을 변경하는 것을 고려하세요."
                        )
                    
                    print(f"❌ Raw 데이터 기간 부족 감지: {oldest_date} > {expected_start_date}")
                    return validation_result
                else:
                    print(f"✅ Raw 데이터 기간 충분: {oldest_date} <= {expected_start_date}")
                    validation_result["data_validation"]["recommendation"] = f"✅ 요청한 기간({expected_start_date}~{expected_end_date})의 데이터가 충분히 포함되어 있습니다."
                    
        except Exception as date_error:
            print(f"⚠️ Raw 데이터 기간 검증 중 오류: {date_error}")
            validation_result["data_validation"]["recommendation"] = f"⚠️ 기간 검증 중 오류 발생: {date_error}. 데이터는 정상적으로 수집되었습니다."
        
        return validation_result



    def process_api_response(self, raw_data: Dict[str, Any], stock_code: str, chart_type: str, chart_params: str = None, expected_start_date: str = None, expected_end_date: str = None) -> Dict[str, Any]:
        """
        키움 API 응답 전체 처리 (저장 + raw 검증 + 필터링)
        
        Args:
            raw_data: 키움 API 원본 응답
            stock_code: 종목코드
            chart_type: 차트 유형 (tick, minute, day, week, month, year)
            chart_params: 차트 파라미터 (틱/분봉: scope, 일/주/월/년봉: None)
            expected_start_date: 예상 시작일 (YYYYMMDD, 선택적)
            expected_end_date: 예상 종료일 (YYYYMMDD, 선택적)
            
        Returns:
            Dict: 필터링된 데이터 + 검증 결과 또는 업그레이드 제안
        """
        filename = f"{stock_code}_{chart_type}"
        
        print(f"🔄 {chart_type.upper()} 차트 데이터 처리 시작: {stock_code}")
        
        # 1. 원본 데이터 저장
        self.save_raw_data(raw_data, filename)
        
        # 2. Raw 데이터에서 먼저 기간 검증 (효율성 최적화)
        raw_validation = self._validate_raw_data_coverage(raw_data, chart_type, chart_params, expected_start_date, expected_end_date)
        
        # 3. Raw 검증에서 문제 발견 시 바로 업그레이드 제안 리턴 (필터링 스킵)
        if not raw_validation["data_validation"]["is_complete"]:
            print(f"❌ Raw 데이터 검증 실패: 필터링 작업 스킵하고 업그레이드 제안")
            
            # 메타데이터만 포함한 간단한 응답
            upgrade_response = {
                "metadata": {
                    "filtered_at": datetime.now().isoformat(),
                    "chart_type": chart_type,
                    "api_function": self.chart_configs.get(chart_type, {}).get("api_function", "unknown"),
                    "original_size": len(str(raw_data)),
                    "api_response_code": raw_data.get("rt_cd", "Unknown"),
                    "stock_code": stock_code,
                    "date_range_filter": f"{expected_start_date}~{expected_end_date}" if expected_start_date and expected_end_date else "none",
                    "processing_skipped": "raw_validation_failed"
                },
                "chart_data": [],  # 빈 데이터
                "data_count": 0
            }
            upgrade_response.update(raw_validation)
            return upgrade_response
        
        print(f"✅ Raw 데이터 검증 통과: 필터링 작업 진행")
        
        # 4. 차트 유형별 데이터 필터링 (Raw 검증 통과 시에만)
        filtered_data = self.filter_chart_data(raw_data, chart_type, expected_start_date, expected_end_date)
        
        # 5. 필터링된 데이터에 성공 검증 결과 추가
        filtered_data["data_validation"] = {
            "is_complete": True,
            "data_coverage": "complete",
            "recommendation": f"✅ 필터링 완료: {len(filtered_data.get('chart_data', []))}개 레코드 처리됨.",
            "chart_upgrade_suggestion": None
        }
        
        # 6. 필터링된 데이터 저장
        self.save_filtered_data(filtered_data, filename)
        
        return filtered_data
    
    def get_data_summary(self) -> Dict[str, Any]:
        """현재 저장된 데이터 요약 정보 반환"""
        summary = {
            "raw_files": len(list(self.raw_dir.glob("*.json"))) if self.raw_dir.exists() else 0,
            "filtered_files": len(list(self.filtered_dir.glob("*.json"))) if self.filtered_dir.exists() else 0,
            "total_size_mb": 0,
            "chart_types_supported": list(self.chart_configs.keys()),
            "last_updated": None
        }
        
        # 총 크기 계산
        total_size = 0
        for dir_path in [self.raw_dir, self.filtered_dir]:
            if dir_path.exists():
                for file_path in dir_path.rglob("*.json"):
                    total_size += file_path.stat().st_size
        
        summary["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return summary
    
    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """특정 차트 유형의 설정 정보 반환 (디버깅용)"""
        return self.chart_configs.get(chart_type, {})


# 전역 데이터 매니저 인스턴스
_data_manager = None

def get_data_manager() -> StockDataManager:
    """전역 데이터 매니저 인스턴스 반환"""
    global _data_manager
    if _data_manager is None:
        _data_manager = StockDataManager()
    return _data_manager 

def process_api_response_for_tools(raw_data: Dict[str, Any], stock_code: str, chart_type: str, chart_params: str = None, expected_start_date: str = None, expected_end_date: str = None) -> str:
    """
    키움 API 응답을 처리하고 필터링된 데이터를 반환 (LangChain 도구 전용)
    
    Args:
        raw_data: 키움 API 원본 응답
        stock_code: 종목코드  
        chart_type: 차트 유형
        chart_params: 차트 파라미터 (틱/분봉: scope, 일/주/월/년봉: None)
        expected_start_date: 예상 시작일 (YYYYMMDD, 선택적)
        expected_end_date: 예상 종료일 (YYYYMMDD, 선택적)
        
    Returns:
        str: 필터링된 데이터 + 검증 결과 JSON 문자열
    """
    try:
        # 기간 정보 로그 출력
        if expected_start_date and expected_end_date:
            print(f"🔍 기간 검증 활성화: {expected_start_date} ~ {expected_end_date}")
        else:
            print(f"ℹ️  기간 검증 생략 (기간 정보 없음)")
        
        # 데이터 처리 (저장 + 필터링 + 검증 통합)
        data_manager = get_data_manager()
        filtered_data = data_manager.process_api_response(
            raw_data, stock_code, chart_type, chart_params, expected_start_date, expected_end_date
        )
        
        return json.dumps(filtered_data, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ 데이터 처리 오류: {e}")
        # 오류 시 원본 데이터 반환 (토큰 문제 발생 가능하지만 시스템 중단 방지)
        return json.dumps(raw_data, ensure_ascii=False) 