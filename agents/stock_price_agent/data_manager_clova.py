"""
Simplified data manager for ChatClovaX agent
Saves chart data to JSON files and returns pandas DataFrames
Includes upgrade suggestions when data is insufficient for requested date range
"""

import os
import json
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class StockDataManager:
    """Simplified data manager for stock chart data with upgrade suggestions for insufficient data"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            current_dir = Path(__file__).parent
            base_path = current_dir / "data"
        
        self.data_dir = Path(base_path)
        self.raw_dir = self.data_dir / "raw"
        self.filtered_dir = self.data_dir / "filtered"
        
        # Chart type configurations
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
        
        # Technical indicator configurations for different chart types
        self.indicator_configs = self._setup_indicator_configs()
        
        self._init_directories()
    
    def _setup_indicator_configs(self):
        """Setup technical indicator parameters for different chart types and timeframes"""
        return {
            "minute_1_3_5": {
                "sma_periods": [9, 20, 50],
                "ema_periods": [9, 20, 50], 
                "macd": {"fast": 6, "slow": 13, "signal": 5},
                "rsi": 9,
                "stoch": {"k": 9, "d": 3},
                "bollinger": {"n": 20, "std": 2},
                "atr": 9,
                "cmf": 20
            },
            "minute_10_15": {
                "sma_periods": [20, 50, 100],
                "ema_periods": [20, 50, 100],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "rsi": 14,
                "stoch": {"k": 14, "d": 3},
                "bollinger": {"n": 20, "std": 2},
                "atr": 14,
                "cmf": 20
            },
            "minute_30_45_60": {
                "sma_periods": [20, 50, 200],
                "ema_periods": [20, 50, 200],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "rsi": 14,
                "stoch": {"k": 14, "d": 3},
                "bollinger": {"n": 20, "std": 2},
                "atr": 14,
                "cmf": 20
            },
            "day": {
                "sma_periods": [20, 50, 200],
                "ema_periods": [20, 50, 200],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "rsi": 14,
                "stoch": {"k": 14, "d": 3},
                "bollinger": {"n": 20, "std": 2},
                "atr": 14,
                "cmf": 20
            },
            "week": {
                "sma_periods": [10, 20, 50],
                "ema_periods": [10, 20, 50],
                "macd": {"fast": 6, "slow": 13, "signal": 5},
                "rsi": 9,
                "stoch": {"k": 9, "d": 3},
                "bollinger": {"n": 10, "std": 2},
                "atr": 10,
                "cmf": 10
            },
            "month": {
                "sma_periods": [6, 12, 24],
                "ema_periods": [6, 12, 24],
                "macd": {"fast": 3, "slow": 6, "signal": 3},
                "rsi": 6,
                "stoch": {"k": 6, "d": 3},
                "bollinger": {"n": 6, "std": 2},
                "atr": 6,
                "cmf": 6
            },
            "year": {
                "sma_periods": [3, 5, 10],
                "ema_periods": [3, 5, 10],
                "macd": {"fast": 2, "slow": 5, "signal": 2},
                "rsi": 6,
                "stoch": {"k": 6, "d": 3},
                "bollinger": {"n": 6, "std": 2},
                "atr": 6,
                "cmf": 6
            }
        }
    
    def _init_directories(self):
        """Initialize data directories"""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.filtered_dir.mkdir(parents=True, exist_ok=True)
    
    def process_chart_data(self, raw_data: Dict[str, Any], stock_code: str, 
                          chart_type: str, base_date: str = None,
                          expected_start_date: str = None, 
                          expected_end_date: str = None,
                          minute_scope: str = None) -> Dict[str, Any]:
        """
        Process chart data from Kiwoom API with upgrade suggestions when data is insufficient
        
        Args:
            raw_data: Raw API response
            stock_code: Stock symbol (e.g., "005930")
            chart_type: Chart type (minute, day, week, month, year)
            base_date: Base date for the request
            expected_start_date: Expected start date (YYYYMMDD)
            expected_end_date: Expected end date (YYYYMMDD)
            
        Returns:
            Dict: Processing result with data or upgrade suggestions for insufficient data
        """
        # 1. Save raw data with proper naming convention
        raw_filepath = self._save_raw_data(raw_data, stock_code, chart_type, base_date)
        
        # 2. If date range filtering is requested
        if expected_start_date and expected_end_date:
            # Check oldest date in raw data
            oldest_date = self._find_oldest_date_in_raw_data(raw_data, chart_type)
            
            if oldest_date and oldest_date > expected_start_date:
                # Data doesn't go back far enough - suggest upgrade
                upgrade_info = self._get_chart_upgrade_suggestion(chart_type)
                
                return {
                    "status": "upgrade_required",
                    "message": f"데이터 부족: 가장 오래된 데이터({oldest_date}) > 요청 시작일({expected_start_date})",
                    "upgrade_suggestion": upgrade_info,
                    "original_start_date": expected_start_date,
                    "original_end_date": expected_end_date,
                    "data": None
                }
            
            # Filter data by date range
            filtered_records = self._filter_data_by_date_range(
                raw_data, chart_type, expected_start_date, expected_end_date
            )
            
            if not filtered_records:
                return {
                    "status": "no_data",
                    "message": "지정된 날짜 범위에 데이터가 없습니다.",
                    "data": None
                }
            
            # Convert filtered data to DataFrame (no data quantity limit)
            # Apply date format conversion for chart type first
            filtered_records = self._convert_date_format_for_chart_type(filtered_records, chart_type)
            
            # Check if records are sufficient (minimum 10 records)
            if len(filtered_records) < 10:
                downgrade_info = self._get_chart_downgrade_suggestion(chart_type, minute_scope)
                
                return {
                    "status": "downgrade_required",
                    "message": f"레코드 부족: {len(filtered_records)}개 < 10개 최소 요구량",
                    "downgrade_suggestion": downgrade_info,
                    "original_start_date": expected_start_date,
                    "original_end_date": expected_end_date,
                    "data": None
                }
            
            df = self._convert_to_dataframe(filtered_records, chart_type)
            
            # Add technical indicators
            df = self._add_technical_indicators(df, chart_type, minute_scope)
            
            # Save filtered data to CSV
            filtered_filepath = self._save_filtered_data_csv(
                df, stock_code, chart_type, base_date, expected_start_date, expected_end_date
            )
            
            return {
                "status": "success",
                "message": f"데이터 처리 완료: {len(df)}개 레코드",
                "data": df
            }
        
        else:
            # No filtering - convert all data to DataFrame and save to CSV
            df = self._extract_chart_dataframe(raw_data, chart_type)
            
            # Add technical indicators
            df = self._add_technical_indicators(df, chart_type, minute_scope)
            
            # Save all processed data to CSV
            filtered_filepath = self._save_filtered_data_csv(
                df, stock_code, chart_type, base_date
            )
            
            return {
                "status": "success",
                "message": f"데이터 처리 완료: {len(df)}개 레코드",
                "data": df
            }
    
    def format_tool_response(self, result: Dict[str, Any], stock_code: str, chart_type: str) -> str:
        """
        Unified response formatting for all tools
        Handles upgrade suggestions for insufficient data and DataFrame table formatting
        
        Args:
            result: Result from process_chart_data()
            stock_code: Stock symbol
            chart_type: Chart type description (e.g., "daily", "5-minute")
            
        Returns:
            str: Formatted response string
        """
        status = result.get("status", "unknown")
        
        if status == "upgrade_required":
            upgrade_info = result.get("upgrade_suggestion", {})
            next_type = upgrade_info.get("next_type")
            description = upgrade_info.get("description", "")
            original_start = result.get("original_start_date")
            original_end = result.get("original_end_date")
            
            response = f"{result.get('message', '')} \n\n"
            response += f"업그레이드 제안: {description}\n"
            if next_type:
                if original_start and original_end:
                    response += f"권장 툴: get_{next_type}_chart(stock_code='{stock_code}', expected_start_date='{original_start}', expected_end_date='{original_end}')\n"
                else:
                    response += f"권장 툴: get_{next_type}_chart(stock_code='{stock_code}')\n"
            
            return response
        
        elif status == "downgrade_required":
            downgrade_info = result.get("downgrade_suggestion", {})
            next_type = downgrade_info.get("next_type")
            next_scope = downgrade_info.get("next_scope")
            description = downgrade_info.get("description", "")
            original_start = result.get("original_start_date")
            original_end = result.get("original_end_date")
            
            response = f"{result.get('message', '')} \n\n"
            response += f"다운그레이드 제안: {description}\n"
            if next_type == "minute" and next_scope:
                if original_start and original_end:
                    response += f"권장 툴: get_minute_chart(stock_code='{stock_code}', minute_scope='{next_scope}', expected_start_date='{original_start}', expected_end_date='{original_end}')\n"
                else:
                    response += f"권장 툴: get_minute_chart(stock_code='{stock_code}', minute_scope='{next_scope}')\n"
            elif next_type and next_type != "minute":
                if original_start and original_end:
                    response += f"권장 툴: get_{next_type}_chart(stock_code='{stock_code}', expected_start_date='{original_start}', expected_end_date='{original_end}')\n"
                else:
                    response += f"권장 툴: get_{next_type}_chart(stock_code='{stock_code}')\n"
            
            return response
        
        elif status == "success":
            df = result.get("data")
            if df is not None and not df.empty:
                response = f"✅ **{chart_type} 차트 데이터** ({stock_code}):\n\n"
                response += self._format_dataframe_table(df)
                return response
            else:
                return f"No {chart_type} chart data available for {stock_code}"
        
        elif status == "no_data":
            return f"❌ {result.get('message', 'No data available')}"
        
        else:
            return f"❌ Unknown status: {status}"
    
    def _format_dataframe_table(self, df: pd.DataFrame) -> str:
        """Format DataFrame as complete table without summary info"""
        if df.empty:
            return "No data available"
        
        # Return complete DataFrame as table string
        return df.to_string(index=False, max_cols=None, max_rows=None)
    
    def _save_raw_data(self, raw_data: Dict[str, Any], stock_code: str, 
                      chart_type: str, base_date: str = None) -> str:
        """Save raw data with proper naming convention: {요청시간}_{api-id}_{주식종목}_{base_date}.json"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        api_id = self.chart_configs.get(chart_type, {}).get("api_function", "unknown")
        base_date_str = base_date if base_date else "nodate"
        
        filename = f"{timestamp}_{api_id}_{stock_code}_{base_date_str}.json"
        filepath = self.raw_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            print(f"Raw data saved: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"❌ Failed to save raw data: {e}")
            return ""
    
    def _find_oldest_date_in_raw_data(self, raw_data: Dict[str, Any], chart_type: str) -> Optional[str]:
        """Find the oldest date in raw data"""
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
                    # Extract YYYYMMDD from datetime if needed
                    if len(record_date) > 8:
                        record_date = record_date[:8]
                    
                    if oldest_date is None or record_date < oldest_date:
                        oldest_date = record_date
        
        return oldest_date
    
    def _get_chart_upgrade_suggestion(self, current_chart_type: str) -> Dict[str, str]:
        """Get chart upgrade suggestion"""
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
    
    def _get_chart_downgrade_suggestion(self, current_chart_type: str, minute_scope: str = None) -> Dict[str, str]:
        """
        Get chart downgrade suggestion for insufficient records
        
        Args:
            current_chart_type: Current chart type
            minute_scope: Current minute scope for minute charts
            
        Returns:
            Dict: Downgrade suggestion info
        """
        if current_chart_type == "minute" and minute_scope:
            # 분봉 다운그레이드: 60→45→30→15→10→5→3→1
            minute_val = int(minute_scope)
            downgrade_map = {
                60: {"next_scope": "45", "description": "60분봉 → 45분봉으로 차트 간격 축소"},
                45: {"next_scope": "30", "description": "45분봉 → 30분봉으로 차트 간격 축소"},
                30: {"next_scope": "15", "description": "30분봉 → 15분봉으로 차트 간격 축소"},
                15: {"next_scope": "10", "description": "15분봉 → 10분봉으로 차트 간격 축소"},
                10: {"next_scope": "5", "description": "10분봉 → 5분봉으로 차트 간격 축소"},
                5: {"next_scope": "3", "description": "5분봉 → 3분봉으로 차트 간격 축소"},
                3: {"next_scope": "1", "description": "3분봉 → 1분봉으로 차트 간격 축소"},
                1: {"next_scope": None, "description": "1분봉이 최소 간격입니다. 기간을 늘리거나 분석 방법을 변경하세요."}
            }
            
            suggestion = downgrade_map.get(minute_val, {"next_scope": None, "description": "다운그레이드 옵션이 없습니다."})
            if suggestion["next_scope"]:
                suggestion["next_type"] = "minute"
            else:
                suggestion["next_type"] = None
            
            return suggestion
        
        else:
            # 일반 차트 다운그레이드: 년→월→주→일→분(60분)
            downgrade_map = {
                "year": {"next_type": "month", "description": "년봉 → 월봉으로 차트 유형 변경"},
                "month": {"next_type": "week", "description": "월봉 → 주봉으로 차트 유형 변경"},
                "week": {"next_type": "day", "description": "주봉 → 일봉으로 차트 유형 변경"},
                "day": {"next_type": "minute", "next_scope": "60", "description": "일봉 → 60분봉으로 차트 유형 변경"}
            }
            
            return downgrade_map.get(current_chart_type, {
                "next_type": None, 
                "description": "다운그레이드 옵션이 없습니다."
            })
    
    def _filter_data_by_date_range(self, raw_data: Dict[str, Any], chart_type: str,
                                  expected_start_date: str, expected_end_date: str) -> list:
        """Filter data by date range and extract core fields"""
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
                        # Extract YYYYMMDD from datetime if needed
                        if len(record_date_str) > 8:
                            record_date_str = record_date_str[:8]
                        
                        try:
                            record_date = datetime.strptime(record_date_str, "%Y%m%d")
                            
                            # Check if date is in range
                            if filter_start <= record_date <= filter_end:
                                # Extract core fields
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
            
            print(f"Date filtering complete: {len(filtered_records)} records")
            return filtered_records
            
        except ValueError as e:
            print(f"❌ Date parsing error: {e}")
            return []
    
    def _convert_to_dataframe(self, records: list, chart_type: str) -> pd.DataFrame:
        """Convert filtered records to DataFrame"""
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Standardize column names
        date_field = "dt" if chart_type != "minute" else "cntr_tm"
        column_mapping = {
            date_field: 'date',
            'cur_prc': 'close',
            'open_pric': 'open', 
            'high_pric': 'high',
            'low_pric': 'low',
            'trde_qty': 'volume',
            'trde_prica': 'amount'
        }
        
        # Rename columns that exist
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)
        
        # Convert numeric columns
        numeric_columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Process date column
        if 'date' in df.columns:
            df['date'] = self._process_date_column(df['date'], chart_type)
        
        # Select and reorder columns
        standard_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns].copy()
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _extract_chart_dataframe(self, raw_data: Dict[str, Any], 
                                chart_type: str) -> pd.DataFrame:
        """Extract chart data and convert to DataFrame (for non-filtered data)"""
        
        # Map chart types to data keys and date fields
        data_mapping = {
            "minute": {"key": "stk_min_pole_chart_qry", "date_field": "cntr_tm"},
            "day": {"key": "stk_dt_pole_chart_qry", "date_field": "dt"},
            "week": {"key": "stk_stk_pole_chart_qry", "date_field": "dt"},
            "month": {"key": "stk_mth_pole_chart_qry", "date_field": "dt"},
            "year": {"key": "stk_yr_pole_chart_qry", "date_field": "dt"}
        }
        
        if chart_type not in data_mapping:
            return pd.DataFrame()
        
        mapping = data_mapping[chart_type]
        data_key = mapping["key"]
        date_field = mapping["date_field"]
        
        # Extract chart records
        chart_records = raw_data.get(data_key, [])
        if not chart_records:
            return pd.DataFrame()
        
        # Apply date format conversion for chart type before DataFrame conversion
        chart_records = self._convert_date_format_for_chart_type(chart_records, chart_type)
        
        # Convert to DataFrame
        df = pd.DataFrame(chart_records)
        
        # Standardize column names
        column_mapping = {
            date_field: 'date',
            'cur_prc': 'close',
            'open_pric': 'open', 
            'high_pric': 'high',
            'low_pric': 'low',
            'trde_qty': 'volume',
            'trde_prica': 'amount'
        }
        
        # Rename columns that exist
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)
        
        # Convert numeric columns
        numeric_columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Process date column
        if 'date' in df.columns:
            df['date'] = self._process_date_column(df['date'], chart_type)
        
        # Select and reorder columns
        standard_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns].copy()
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _process_date_column(self, date_series: pd.Series, chart_type: str) -> pd.Series:
        """Process date column based on chart type"""
        
        if chart_type == "minute":
            # For minute data, keep datetime format
            return pd.to_datetime(date_series, format='%Y%m%d%H%M%S', errors='coerce')
        
        elif chart_type == "day":
            # For daily data, convert to date
            return pd.to_datetime(date_series, format='%Y%m%d', errors='coerce').dt.date
        
        elif chart_type == "week":
            # For weekly data, keep as string (e.g., "202412Week5")
            return date_series.astype(str)
        
        elif chart_type == "month":
            # For monthly data, convert YYYYMM to date
            return pd.to_datetime(date_series, format='%Y%m', errors='coerce').dt.date
        
        elif chart_type == "year":
            # For yearly data, convert YYYY to date
            return pd.to_datetime(date_series, format='%Y', errors='coerce').dt.date
        
        else:
            return date_series
    
    def _convert_date_format_for_chart_type(self, filtered_records: list, chart_type: str) -> list:
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
    
    def _get_indicator_config_key(self, chart_type: str, minute_scope: str = None) -> str:
        """Get indicator configuration key based on chart type and minute scope"""
        if chart_type == "minute" and minute_scope:
            minute_val = int(minute_scope)
            if minute_val in [1, 3, 5]:
                return "minute_1_3_5"
            elif minute_val in [10, 15]:
                return "minute_10_15"
            elif minute_val in [30, 45, 60]:
                return "minute_30_45_60"
        
        return chart_type  # day, week, month, year
    
    def _add_technical_indicators(self, df: pd.DataFrame, chart_type: str, minute_scope: str = None) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame based on chart type and timeframe
        
        Args:
            df: DataFrame with OHLCV data
            chart_type: Chart type (minute, day, week, month, year)
            minute_scope: Minute scope for minute charts (1, 3, 5, 10, 15, 30, 45, 60)
            
        Returns:
            pd.DataFrame: DataFrame with technical indicators added
        """
        if df.empty or len(df) < 10:  # Need minimum data for indicators
            print("⚠️  Insufficient data for technical indicators")
            return df
        
        # Get indicator configuration
        config_key = self._get_indicator_config_key(chart_type, minute_scope)
        config = self.indicator_configs.get(config_key, self.indicator_configs["day"])
        
        # Create a copy to avoid modifying original
        df_with_indicators = df.copy()
        
        try:
            # Ensure required columns exist and are numeric
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df_with_indicators.columns:
                    print(f"⚠️  Missing {col} column for technical indicators")
                    return df
                df_with_indicators[col] = pd.to_numeric(df_with_indicators[col], errors='coerce')
            
            # Remove rows with NaN values in OHLCV columns
            df_with_indicators = df_with_indicators.dropna(subset=required_cols)
            
            if len(df_with_indicators) < 10:
                print("⚠️  Insufficient valid data after cleaning")
                return df
            
            # Calculate SMA (Simple Moving Averages)
            for period in config["sma_periods"]:
                if len(df_with_indicators) >= period:
                    df_with_indicators[f'sma_{period}'] = ta.sma(df_with_indicators['close'], length=period)
            
            # Calculate EMA (Exponential Moving Averages)
            for period in config["ema_periods"]:
                if len(df_with_indicators) >= period:
                    df_with_indicators[f'ema_{period}'] = ta.ema(df_with_indicators['close'], length=period)
            
            # Calculate MACD
            macd_params = config["macd"]
            if len(df_with_indicators) >= macd_params["slow"]:
                macd_result = ta.macd(
                    df_with_indicators['close'], 
                    fast=macd_params["fast"], 
                    slow=macd_params["slow"], 
                    signal=macd_params["signal"]
                )
                if macd_result is not None and not macd_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, macd_result], axis=1)
            
            # Calculate RSI
            if len(df_with_indicators) >= config["rsi"]:
                df_with_indicators['rsi'] = ta.rsi(df_with_indicators['close'], length=config["rsi"])
            
            # Calculate Stochastic
            stoch_params = config["stoch"]
            if len(df_with_indicators) >= stoch_params["k"]:
                stoch_result = ta.stoch(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'],
                    k=stoch_params["k"],
                    d=stoch_params["d"]
                )
                if stoch_result is not None and not stoch_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, stoch_result], axis=1)
            
            # Calculate Bollinger Bands
            bb_params = config["bollinger"]
            if len(df_with_indicators) >= bb_params["n"]:
                bb_result = ta.bbands(
                    df_with_indicators['close'], 
                    length=bb_params["n"], 
                    std=bb_params["std"]
                )
                if bb_result is not None and not bb_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, bb_result], axis=1)
            
            # Calculate ATR (Average True Range)
            if len(df_with_indicators) >= config["atr"]:
                df_with_indicators['atr'] = ta.atr(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'], 
                    length=config["atr"]
                )
            
            # Calculate CMF (Chaikin Money Flow)
            if len(df_with_indicators) >= config["cmf"]:
                df_with_indicators['cmf'] = ta.cmf(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'], 
                    df_with_indicators['volume'], 
                    length=config["cmf"]
                )
            
            print(f"✅ Technical indicators added: {len(df_with_indicators.columns) - len(df.columns)} new columns")
            return df_with_indicators
            
        except Exception as e:
            print(f"❌ Error calculating technical indicators: {e}")
            return df
    
    def _save_filtered_data_csv(self, df: pd.DataFrame, stock_code: str, chart_type: str, 
                               base_date: str = None, expected_start_date: str = None, 
                               expected_end_date: str = None) -> str:
        """
        Save filtered DataFrame to CSV format only
        
        Args:
            df: Filtered DataFrame to save
            stock_code: Stock symbol
            chart_type: Chart type (minute, day, week, month, year)
            base_date: Base date for the request
            expected_start_date: Expected start date (YYYYMMDD)
            expected_end_date: Expected end date (YYYYMMDD)
            
        Returns:
            str: Saved CSV file path
        """
        if df.empty:
            print("⚠️  Empty DataFrame - not saving filtered data")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        api_id = self.chart_configs.get(chart_type, {}).get("api_function", "unknown")
        base_date_str = base_date if base_date else "nodate"
        
        # Create filename with date range if available
        if expected_start_date and expected_end_date:
            date_range = f"{expected_start_date}_{expected_end_date}"
            filename = f"{timestamp}_{api_id}_{stock_code}_{base_date_str}_{date_range}.csv"
        else:
            filename = f"{timestamp}_{api_id}_{stock_code}_{base_date_str}_all.csv"
        
        csv_filepath = self.filtered_dir / filename
        
        try:
            # Save as CSV (human readable, Excel compatible)
            df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
            csv_size = csv_filepath.stat().st_size
            
            print(f"✅ CSV saved: {csv_filepath}")
            print(f"📊 Saved {len(df)} records with {len(df.columns)} columns")
            print(f"💾 CSV size: {csv_size:,} bytes")
            
            return str(csv_filepath)
            
        except Exception as e:
            print(f"❌ Failed to save CSV data: {e}")
            return ""


# Global data manager instance
_data_manager = None

def get_data_manager() -> StockDataManager:
    """Get global data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = StockDataManager()
    return _data_manager 