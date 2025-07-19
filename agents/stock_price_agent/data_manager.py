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
        
        self._init_directories()
    
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
            minute_scope: Minute scope for minute charts
            
        Returns:
            Dict: Processing result with data or upgrade suggestions for insufficient data
        """
        # 1. Save raw data with proper naming convention
        raw_filepath = self._save_raw_data(raw_data, stock_code, chart_type, base_date)
        
        # 2. Convert ALL raw data to DataFrame with date format conversion
        df = self._extract_chart_dataframe(raw_data, chart_type)
        
        if df.empty:
            return {
                "status": "no_data",
                "message": "원본 데이터가 비어있습니다.",
                "data": None
            }
        
        # 3. Add technical indicators to FULL dataset
        df = self._add_technical_indicators(df, chart_type, minute_scope)
        
        # 4. Apply date filtering if requested
        if expected_start_date and expected_end_date:
            # Check oldest date in dataframe first
            oldest_date = self._find_oldest_date_in_dataframe(df, chart_type)
            
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
            
            # Filter dataframe by date range
            df_filtered = self._filter_dataframe_by_date_range(
                df, chart_type, expected_start_date, expected_end_date
            )
            
            if df_filtered.empty:
                return {
                    "status": "no_data",
                    "message": "지정된 날짜 범위에 데이터가 없습니다.",
                    "data": None
                }
            
            # Check if filtered records are sufficient (minimum 10 records)
            if len(df_filtered) < 10:
                downgrade_info = self._get_chart_downgrade_suggestion(chart_type, minute_scope)
                
                return {
                    "status": "downgrade_required",
                    "message": f"레코드 부족: {len(df_filtered)}개 < 10개 최소 요구량",
                    "downgrade_suggestion": downgrade_info,
                    "original_start_date": expected_start_date,
                    "original_end_date": expected_end_date,
                    "data": None
                }
            
            # Use filtered dataframe
            df = df_filtered
        
        # Apply chart-specific date format after filtering
        df = self._convert_date_format_for_chart_type(df, chart_type)
        
        # 5. Save processed data to CSV
        filtered_filepath = self._save_filtered_data_csv(
            df, stock_code, chart_type, base_date, expected_start_date, expected_end_date
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
    
    def _find_oldest_date_in_dataframe(self, df: pd.DataFrame, chart_type: str) -> Optional[str]:
        """
        Find the oldest date in DataFrame
        
        Args:
            df: DataFrame with date column (YYYYMMDD string format)
            chart_type: Chart type
            
        Returns:
            str: Oldest date in YYYYMMDD format or None
        """
        if df.empty or 'date' not in df.columns:
            return None
        
        try:
            # All dates are now strings (YYYYMMDD format)
            oldest_date_str = df['date'].min()
            if pd.isna(oldest_date_str) or not isinstance(oldest_date_str, str):
                return None
            
            # For all chart types, return the date string as-is or extract YYYYMMDD
            if chart_type in ["minute", "day"]:
                # For minute/day data, date should be YYYYMMDD or YYYYMMDDHHMISS
                if len(oldest_date_str) >= 8:
                    return oldest_date_str[:8]  # Extract YYYYMMDD
                return oldest_date_str
            
            elif chart_type == "week":
                # For weekly data, extract YYYYMMDD from YYYYMMWeekN format if already converted
                # or return YYYYMMDD if not yet converted
                if "Week" in oldest_date_str and len(oldest_date_str) >= 6:
                    return oldest_date_str[:6] + "01"  # Return first day of month
                elif len(oldest_date_str) >= 8:
                    return oldest_date_str[:8]  # YYYYMMDD
                return oldest_date_str
            
            elif chart_type in ["month", "year"]:
                # For monthly/yearly data, should be YYYYMMDD format before conversion
                if len(oldest_date_str) >= 8:
                    return oldest_date_str[:8]  # YYYYMMDD
                return oldest_date_str
            
            return oldest_date_str
            
        except Exception as e:
            print(f"❌ Error finding oldest date in dataframe: {e}")
            return None
    
    def _filter_dataframe_by_date_range(self, df: pd.DataFrame, chart_type: str,
                                       expected_start_date: str, expected_end_date: str) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: DataFrame with date column (YYYYMMDD string format)
            chart_type: Chart type
            expected_start_date: Start date (YYYYMMDD)
            expected_end_date: End date (YYYYMMDD)
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if df.empty or 'date' not in df.columns:
            return pd.DataFrame()
        
        try:
            # All dates are now strings (YYYYMMDD format), so we can use string comparison
            def extract_date_for_comparison(date_str, chart_type):
                """Extract YYYYMMDD string for comparison"""
                if pd.isna(date_str) or not isinstance(date_str, str):
                    return None
                
                if chart_type in ["minute", "day"]:
                    # For minute/day data, extract YYYYMMDD
                    if len(date_str) >= 8:
                        return date_str[:8]  # YYYYMMDD
                    return date_str
                
                elif chart_type == "week":
                    # For weekly data, could be YYYYMMWeekN or YYYYMMDD
                    if "Week" in date_str and len(date_str) >= 6:
                        # Extract YYYYMM and use first day of month
                        return date_str[:6] + "01"  # YYYYMM + 01
                    elif len(date_str) >= 8:
                        return date_str[:8]  # YYYYMMDD
                    return date_str
                
                elif chart_type in ["month", "year"]:
                    # For monthly/yearly data, should be YYYYMMDD before conversion
                    if len(date_str) >= 8:
                        return date_str[:8]  # YYYYMMDD
                    return date_str
                
                return date_str
            
            # Extract comparable dates
            df_temp = df.copy()
            df_temp['comparable_date'] = df_temp['date'].apply(
                lambda x: extract_date_for_comparison(x, chart_type)
            )
            
            # Filter using string comparison (YYYYMMDD strings can be compared lexicographically)
            mask = (df_temp['comparable_date'] >= expected_start_date) & (df_temp['comparable_date'] <= expected_end_date)
            mask = mask & df_temp['comparable_date'].notna()  # Remove NaN values
            
            filtered_df = df[mask].copy().reset_index(drop=True)
            print(f"📅 DataFrame 날짜 필터링 완료: {len(filtered_df)}개 레코드")
            return filtered_df
            
        except Exception as e:
            print(f"❌ DataFrame 날짜 필터링 오류: {e}")
            return pd.DataFrame()
    
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
        
        # Convert to DataFrame (without date format conversion yet)
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
        
        # Keep date column as string (YYYYMMDD format)
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
        
        # Select and reorder columns
        standard_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        available_columns = [col for col in standard_columns if col in df.columns]
        df = df[available_columns].copy()
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _convert_date_format_for_chart_type(self, data, chart_type: str):
        """
        차트 유형에 맞게 날짜 형식을 변환합니다
        
        Args:
            data: 차트 데이터 (list of records 또는 pandas DataFrame)
            chart_type: 차트 유형
            
        Returns:
            List or DataFrame: 날짜 형식이 변환된 차트 데이터 (입력 타입과 동일)
        """
        # DataFrame인 경우
        if isinstance(data, pd.DataFrame):
            if data.empty or 'date' not in data.columns:
                return data
            
            df_copy = data.copy()
            
            if chart_type == "minute":
                # For minute data, convert to datetime format
                df_copy['date'] = pd.to_datetime(df_copy['date'], format='%Y%m%d%H%M%S', errors='coerce')
                
            elif chart_type == "day":
                # For daily data, convert to date format
                df_copy['date'] = pd.to_datetime(df_copy['date'], format='%Y%m%d', errors='coerce').dt.date
            
            elif chart_type == "week":
                # DataFrame의 date 컬럼을 YYYYMMWeekN 형식으로 변환
                def date_to_week_format(date_str):
                    if pd.isna(date_str) or not isinstance(date_str, str):
                        return str(date_str)
                    if len(date_str) >= 8:  # YYYYMMDD 형식
                        year_month = date_str[:6]  # YYYYMM
                        day = date_str[6:8]
                        week_num = (int(day) - 1) // 7 + 1
                        return f"{year_month}Week{week_num}"
                    return str(date_str)
                
                df_copy['date'] = df_copy['date'].apply(date_to_week_format)
                
            elif chart_type == "month":
                # DataFrame의 date 컬럼을 YYYYMM 형식으로 변환
                def date_to_month_format(date_str):
                    if pd.isna(date_str) or not isinstance(date_str, str):
                        return str(date_str)
                    if len(date_str) >= 6:  # YYYYMMDD 형식
                        return date_str[:6]  # YYYYMM
                    return str(date_str)
                
                df_copy['date'] = df_copy['date'].apply(date_to_month_format)
                
            elif chart_type == "year":
                # DataFrame의 date 컬럼을 YYYY 형식으로 변환
                def date_to_year_format(date_str):
                    if pd.isna(date_str) or not isinstance(date_str, str):
                        return str(date_str)
                    if len(date_str) >= 4:  # YYYYMMDD 형식
                        return date_str[:4]  # YYYY
                    return str(date_str)
                
                df_copy['date'] = df_copy['date'].apply(date_to_year_format)
            
            print(f"📅 DataFrame 날짜 형식 변환 완료: {chart_type} 차트용")
            return df_copy
        
        # List인 경우 (기존 로직 유지)
        filtered_records = data
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
    

    
    def _add_technical_indicators(self, df: pd.DataFrame, chart_type: str, minute_scope: str = None) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame based on chart type and timeframe
        Calculate all indicators first, then filter based on chart type requirements
        
        Args:
            df: DataFrame with OHLCV data
            chart_type: Chart type (minute, day, week, month, year)
            minute_scope: Minute scope for minute charts (1, 3, 5, 10, 15, 30, 45, 60)
            
        Returns:
            pd.DataFrame: DataFrame with required technical indicators only
        """
        if df.empty or len(df) < 10:  # Need minimum data for indicators
            print("⚠️  Insufficient data for technical indicators")
            return df
        
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
            
            # Calculate ALL possible indicators first
            
            # SMA (Simple Moving Averages) - all periods
            all_sma_periods = [10, 20, 50]
            for period in all_sma_periods:
                df_with_indicators[f'sma_{period}'] = ta.sma(df_with_indicators['close'], length=period)
            
            # EMA (Exponential Moving Averages) - all periods  
            all_ema_periods = [10, 20, 50]
            for period in all_ema_periods:
                df_with_indicators[f'ema_{period}'] = ta.ema(df_with_indicators['close'], length=period)
            
            # MACD with 6-13-5 parameters (as specified in table)
            if len(df_with_indicators) >= 13:
                macd_result = ta.macd(
                    df_with_indicators['close'], 
                    fast=6, 
                    slow=13, 
                    signal=5
                )
                if macd_result is not None and not macd_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, macd_result], axis=1)
            
            # RSI
            if len(df_with_indicators) >= 14:
                df_with_indicators['rsi'] = ta.rsi(df_with_indicators['close'], length=14)
            
            # Stochastic with 9-3-3 parameters
            if len(df_with_indicators) >= 9:
                stoch_result = ta.stoch(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'],
                    k=9,
                    d=3
                )
                if stoch_result is not None and not stoch_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, stoch_result], axis=1)
            
            # Bollinger Bands with 10-2.0 parameters
            if len(df_with_indicators) >= 10:
                bb_result = ta.bbands(
                    df_with_indicators['close'], 
                    length=10, 
                    std=2.0
                )
                if bb_result is not None and not bb_result.empty:
                    df_with_indicators = pd.concat([df_with_indicators, bb_result], axis=1)
            
            # ATR (Average True Range)
            if len(df_with_indicators) >= 14:
                df_with_indicators['atr'] = ta.atr(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'], 
                    length=14
                )
            
            # CMF (Chaikin Money Flow)
            if len(df_with_indicators) >= 20:
                df_with_indicators['cmf'] = ta.cmf(
                    df_with_indicators['high'], 
                    df_with_indicators['low'], 
                    df_with_indicators['close'], 
                    df_with_indicators['volume'], 
                    length=20
                )
            
            # Now filter indicators based on chart type according to temp.md table
            df_filtered = self._filter_indicators_by_chart_type(df_with_indicators, chart_type, minute_scope)
            
            print(f"✅ Technical indicators calculated and filtered: {len(df_filtered.columns) - len(df.columns)} indicators kept for {chart_type}")
            return df_filtered
            
        except Exception as e:
            print(f"❌ Error calculating technical indicators: {e}")
            return df
    
    def _filter_indicators_by_chart_type(self, df: pd.DataFrame, chart_type: str, minute_scope: str = None) -> pd.DataFrame:
        """
        Filter indicators based on chart type according to temp.md table
        Maps temp.md indicator names to actual pandas_ta column names
        
        Args:
            df: DataFrame with all indicators calculated
            chart_type: Chart type (minute, day, week, month, year)
            minute_scope: Minute scope for minute charts
            
        Returns:
            pd.DataFrame: DataFrame with only required indicators for the chart type
        """
        # Start with base columns (OHLCV + date)
        base_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        keep_columns = [col for col in base_columns if col in df.columns]
        
        # Mapping from temp.md indicator names to actual column names generated by our code
        # Based on actual available columns: ['sma_10', 'sma_20', 'sma_50', 'ema_10', 'ema_20', 'ema_50', 'MACD_6_13_5', 'MACDh_6_13_5', 'MACDs_6_13_5', 'rsi', 'STOCHk_9_3_3', 'STOCHd_9_3_3', 'BBL_10_2.0', 'BBM_10_2.0', 'BBU_10_2.0', 'BBB_10_2.0', 'BBP_10_2.0', 'atr', 'cmf']
        indicator_mapping = {
            'sma_10': 'sma_10',
            'sma_20': 'sma_20', 
            'sma_50': 'sma_50',
            'ema_10': 'ema_10',
            'ema_20': 'ema_20',
            'ema_50': 'ema_50',
            'MACD_6_13_5': 'MACD_6_13_5',
            'MACDh_6_13_5': 'MACDh_6_13_5',
            'MACDs_6_13_5': 'MACDs_6_13_5',
            'rsi': 'rsi',
            'STOCHk_9_3_3': 'STOCHk_9_3_3',
            'STOCHd_9_3_3': 'STOCHd_9_3_3',
            'BBL_10_2.0': 'BBL_10_2.0',
            'BBM_10_2.0': 'BBM_10_2.0',
            'BBU_10_2.0': 'BBU_10_2.0',
            'BBB_10_2.0': 'BBB_10_2.0',
            'BBP_10_2.0': 'BBP_10_2.0',
            'atr': 'atr',
            'cmf': 'cmf'
        }
        
        # Define required indicators for each chart type based on temp.md table
        if chart_type == "minute" and minute_scope:
            minute_val = int(minute_scope)
            if minute_val in [1, 3, 5, 10, 15]:  # 초단기 분봉 (1-15m)
                required_temp_indicators = [
                    'sma_10', 'sma_20', 'ema_10', 'ema_20', 
                    'MACDh_6_13_5', 'rsi', 'STOCHk_9_3_3', 
                    'BBB_10_2.0', 'atr', 'cmf'
                ]
            elif minute_val in [30, 45, 60]:  # 중기 분봉 (30-60m)
                required_temp_indicators = [
                    'sma_10', 'ema_10', 'ema_20', 
                    'MACDh_6_13_5', 'rsi', 'STOCHk_9_3_3', 
                    'BBB_10_2.0', 'atr', 'cmf'
                ]
            else:
                required_temp_indicators = []  # fallback
        
        elif chart_type == "day":  # 일봉
            required_temp_indicators = [
                'sma_20', 'sma_50', 'ema_20', 'ema_50', 
                'MACDh_6_13_5', 'rsi', 'STOCHk_9_3_3', 
                'BBB_10_2.0', 'atr', 'cmf'
            ]
        
        elif chart_type == "week":  # 주봉
            required_temp_indicators = [
                'sma_20', 'sma_50', 'ema_20', 'ema_50', 
                'MACDh_6_13_5', 'rsi', 'BBB_10_2.0', 'atr', 'cmf'
            ]
        
        elif chart_type == "month":  # 월봉
            required_temp_indicators = [
                'MACDh_6_13_5', 'rsi', 'cmf'
            ]
        
        elif chart_type == "year":  # 년봉
            required_temp_indicators = [
                'MACDh_6_13_5', 'rsi', 'cmf'
            ]
        
        else:
            required_temp_indicators = []  # fallback
        
        # Convert temp.md indicator names to actual pandas_ta column names and add to keep_columns
        for temp_indicator in required_temp_indicators:
            actual_column = indicator_mapping.get(temp_indicator)
            if actual_column and actual_column in df.columns:
                keep_columns.append(actual_column)
            else:
                available_cols = [col for col in df.columns if col not in base_columns]
                print(f"⚠️  Required indicator {temp_indicator} (maps to {actual_column}) not found in DataFrame")
                print(f"Available indicator columns: {available_cols}")
        
        # Return filtered DataFrame
        filtered_df = df[keep_columns].copy()
        
        print(f"📊 Filtered indicators for {chart_type}: {len(keep_columns) - len(base_columns)} indicators kept")
        return filtered_df
    
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