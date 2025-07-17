"""
Date utilities for ChatClovaX Stock Price Agent
Calculates date placeholders for prompt formatting
"""

from datetime import datetime, timedelta
from calendar import monthrange
from typing import Dict


def get_today_date() -> str:
    """Get today's date in YYYYMMDD format"""
    return datetime.now().strftime('%Y%m%d')


def calculate_date_placeholders() -> Dict[str, str]:
    """
    Calculate all date placeholders for agent prompt
    
    Returns:
        Dict: Date placeholders in YYYYMMDD format (except years in YYYY)
    """
    today = datetime.now()
    
    # Basic dates
    today_date = get_today_date()
    yesterday_date = (today - timedelta(days=1)).strftime("%Y%m%d")
    tomorrow_date = (today + timedelta(days=1)).strftime("%Y%m%d")
    
    # This month
    this_month_start = today.replace(day=1).strftime("%Y%m%d")
    _, last_day = monthrange(today.year, today.month)
    this_month_end = today.replace(day=last_day).strftime("%Y%m%d")
    
    # Last month
    if today.month == 1:
        last_month = datetime(today.year - 1, 12, 1)
    else:
        last_month = datetime(today.year, today.month - 1, 1)
    
    last_month_start = last_month.strftime("%Y%m%d")
    _, last_month_last_day = monthrange(last_month.year, last_month.month)
    last_month_end = last_month.replace(day=last_month_last_day).strftime("%Y%m%d")
    
    # Next month
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1)
    else:
        next_month = datetime(today.year, today.month + 1, 1)
    
    next_month_start = next_month.strftime("%Y%m%d")
    _, next_month_last_day = monthrange(next_month.year, next_month.month)
    next_month_end = next_month.replace(day=next_month_last_day).strftime("%Y%m%d")
    
    # This year
    this_year_start = datetime(today.year, 1, 1).strftime("%Y%m%d")
    this_year_end = datetime(today.year, 12, 31).strftime("%Y%m%d")
    this_year = str(today.year)  # YYYY format
    
    # Last year
    last_year_num = today.year - 1
    last_year_start = datetime(last_year_num, 1, 1).strftime("%Y%m%d")
    last_year_end = datetime(last_year_num, 12, 31).strftime("%Y%m%d")
    last_year = str(last_year_num)  # YYYY format
    
    return {
        "today_date": today_date,
        "yesterday_date": yesterday_date,
        "tomorrow_date": tomorrow_date,
        "this_month_start": this_month_start,
        "this_month_end": this_month_end,
        "last_month_start": last_month_start,
        "last_month_end": last_month_end,
        "next_month_start": next_month_start,
        "next_month_end": next_month_end,
        "this_year_start": this_year_start,
        "this_year_end": this_year_end,
        "last_year_start": last_year_start,
        "last_year_end": last_year_end,
        "this_year": this_year,
        "last_year": last_year
    }


def format_prompt_with_dates(prompt_template: str) -> str:
    """
    Format prompt template with current date placeholders only
    Leaves tool-related placeholders ({tool_names}, {tools}) for LangGraph to handle
    
    Args:
        prompt_template: Template string with date placeholders
        
    Returns:
        str: Formatted prompt with actual dates, tool placeholders preserved
    """
    date_placeholders = calculate_date_placeholders()
    
    # Only format date placeholders, leave tool placeholders for LangGraph
    try:
        # Use partial formatting - only replace placeholders we have values for
        formatted = prompt_template
        for key, value in date_placeholders.items():
            formatted = formatted.replace(f"{{{key}}}", value)
        return formatted
    except KeyError as e:
        # If there are missing placeholders, return original template
        print(f"⚠️ Warning: Missing placeholder {e} in prompt template")
        return prompt_template 