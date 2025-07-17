"""
Simplified data manager for ChatClovaX agent
Saves chart data to JSON files and returns pandas DataFrames
Includes upgrade suggestions and date filtering from legacy version
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class StockDataManager:
    """Simplified data manager for stock chart data with upgrade features"""
    
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
                          expected_end_date: str = None) -> Dict[str, Any]:
        """
        Process chart data from Kiwoom API with upgrade suggestions
        
        Args:
            raw_data: Raw API response
            stock_code: Stock symbol (e.g., "005930")
            chart_type: Chart type (minute, day, week, month, year)
            base_date: Base date for the request
            expected_start_date: Expected start date (YYYYMMDD)
            expected_end_date: Expected end date (YYYYMMDD)
            
        Returns:
            Dict: Processing result with data/upgrade suggestions
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
                    "raw_file": raw_filepath,
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
                    "raw_file": raw_filepath,
                    "data": None
                }
            
            # Check if too much data (>100 records) - suggest upgrade
            if len(filtered_records) > 100:
                upgrade_info = self._get_chart_upgrade_suggestion(chart_type)
                
                return {
                    "status": "upgrade_recommended", 
                    "message": f"데이터 과다 ({len(filtered_records)}개 > 100개 권장): 더 큰 차트 간격 사용 권장",
                    "upgrade_suggestion": upgrade_info,
                    "data_count": len(filtered_records),
                    "raw_file": raw_filepath,
                    "data": self._convert_to_dataframe(filtered_records, chart_type)
                }
            
            # Convert filtered data to DataFrame
            df = self._convert_to_dataframe(filtered_records, chart_type)
            
        else:
            # No filtering - convert all data to DataFrame
            df = self._extract_chart_dataframe(raw_data, chart_type)
        
        return {
            "status": "success",
            "message": f"데이터 처리 완료: {len(df)}개 레코드",
            "raw_file": raw_filepath,
            "data": df
        }
    
    def format_tool_response(self, result: Dict[str, Any], stock_code: str, chart_type: str) -> str:
        """
        Unified response formatting for all tools
        Handles upgrade suggestions and DataFrame table formatting
        
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
            
            response = f"⚠️ {result.get('message', '')} \n\n"
            response += f"💡 **업그레이드 제안**: {description}\n"
            if next_type:
                response += f"📈 권장 툴: get_{next_type}_chart(stock_code='{stock_code}')\n"
            
            return response
        
        elif status == "upgrade_recommended":
            upgrade_info = result.get("upgrade_suggestion", {})
            description = upgrade_info.get("description", "")
            df = result.get("data")
            
            response = f"⚠️ {result.get('message', '')}\n\n"
            response += f"💡 **업그레이드 권장**: {description}\n\n"
            
            if df is not None and not df.empty:
                response += f"📊 **{chart_type} 차트 데이터** ({stock_code}):\n\n"
                response += self._format_dataframe_table(df)
            
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
            print(f"💾 Raw data saved: {filepath}")
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
            
            print(f"📅 Date filtering complete: {len(filtered_records)} records")
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


# Global data manager instance
_data_manager = None

def get_data_manager() -> StockDataManager:
    """Get global data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = StockDataManager()
    return _data_manager 