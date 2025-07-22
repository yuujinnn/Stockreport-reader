"""
Simplified Kiwoom API module for ChatClovaX agent
Handles authentication and chart data fetching only
"""

import os
import json
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("secrets/.env")

BASE_URL = 'https://api.kiwoom.com'
CHART_ENDPOINT = '/api/dostk/chart'


class KiwoomTokenManager:
    """Simplified token manager for Kiwoom API with complete legacy features"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token_file = "secrets/access_token.json"
        self.appkey = self._load_secret("57295187_appkey.txt")
        self.secretkey = self._load_secret("57295187_secretkey.txt")
    
    def _load_secret(self, filename: str) -> str:
        """Load secret from file"""
        try:
            with open(f"secrets/{filename}", "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"secrets/{filename} file not found")
    
    def _save_token_to_file(self, token_data: Dict):
        """Save token to file with detailed logging"""
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Token saved to {self.token_file}")
        except Exception as e:
            print(f"❌ Token save error: {e}")
    
    def _load_token_from_file(self) -> Optional[Dict]:
        """Load token from file with error handling"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Token load error: {e}")
        return None
    
    def _is_token_valid(self, token_data: Dict) -> bool:
        """Check if token is still valid with detailed logging"""
        if not token_data or 'expires_dt' not in token_data:
            return False
        
        try:
            expires_dt = datetime.strptime(token_data['expires_dt'], '%Y%m%d%H%M%S')
            # Refresh 1 hour before expiry
            buffer_time = timedelta(hours=1)
            current_time = datetime.now()
            
            is_valid = current_time < (expires_dt - buffer_time)
            
            if is_valid:
                remaining = expires_dt - current_time
                print(f"🔑 Token valid: {remaining.total_seconds()/3600:.1f} hours remaining")
            else:
                print(f"⏰ Token expiring soon or expired")
                
            return is_valid
        except ValueError as e:
            print(f"❌ Token expiry date parsing error: {e}")
            return False
    
    def get_access_token(self, force_refresh=False) -> Optional[str]:
        """
        Get valid access token with automatic refresh
        
        Args:
            force_refresh (bool): Force token refresh
            
        Returns:
            str: Valid access token or None
        """
        # Check existing token if not forcing refresh
        if not force_refresh:
            existing_token = self._load_token_from_file()
            if existing_token and self._is_token_valid(existing_token):
                print("✅ Using existing token")
                return existing_token['token']
        
        # Request new token
        print("🔄 Requesting new token...")
        token_data = self._request_new_token()
        
        if token_data and token_data.get('return_code') == 0:
            # Save token to file
            self._save_token_to_file(token_data)
            print("✅ New token issued and saved")
            return token_data['token']
        else:
            error_msg = token_data.get('return_msg', 'Unknown error') if token_data else 'API call failed'
            print(f"❌ Token issuance failed: {error_msg}")
            return None
    
    def _request_new_token(self) -> Optional[Dict]:
        """Request new access token"""
        url = f"{self.base_url}/oauth2/token"
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'appkey': self.appkey,
            'secretkey': self.secretkey
        }
        
        try:
            print(f"Token request: {url}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('return_code') == 0:
                expires_dt = result.get('expires_dt', '')
                print(f"✅ Access token issued successfully")
                print(f"Token expires: {expires_dt}")
                return result
            else:
                print(f"❌ Token issuance failed: {result.get('return_msg')}")
                return result
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API request error: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke access token"""
        url = f"{self.base_url}/oauth2/revoke"
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        data = {
            'token': token,
            'appkey': self.appkey,
            'secretkey': self.secretkey
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('return_code') == 0:
                print("✅ Token revoked successfully")
                # Remove saved token file
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                    print("✅ Token file removed")
                return True
            else:
                print(f"❌ Token revocation failed: {result.get('return_msg')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API request error: {e}")
            return False


def make_api_request_with_retry(tr_code: str, data: Dict, max_retries: int = 1) -> Optional[Dict]:
    """
    Make API request with automatic token refresh on authentication failure
    
    Args:
        tr_code: API transaction code
        data: Request data
        max_retries: Maximum retry attempts (default 1)
        
    Returns:
        Dict: API response or None if failed
    """
    token_manager = get_token_manager()
    
    for attempt in range(max_retries + 1):
        # Get current token (refresh if needed)
        token = token_manager.get_access_token(force_refresh=(attempt > 0))
        
        if not token:
            print(f"❌ Failed to get access token (attempt {attempt + 1})")
            continue
        
        # Make API request
        result = _make_single_api_request(token, tr_code, data)
        
        if result is not None:
            # Check for token authentication errors
            return_code = result.get('return_code', 0)
            return_msg = result.get('return_msg', '')
            
            if return_code == 3 and 'Token' in return_msg:
                print(f"🔄 Token authentication failed (attempt {attempt + 1}): {return_msg}")
                if attempt < max_retries:
                    print("🔄 Retrying with new token...")
                    continue
            
            return result
        else:
            print(f"❌ API request failed (attempt {attempt + 1})")
            if attempt < max_retries:
                print("🔄 Retrying...")
                continue
    
    print(f"❌ All retry attempts failed for {tr_code}")
    return None


def _make_single_api_request(token: str, tr_code: str, data: Dict) -> Optional[Dict]:
    """Make single API request to Kiwoom chart endpoint with detailed logging"""
    url = BASE_URL + CHART_ENDPOINT
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': tr_code,
    }
    
    try:
        print(f"📡 Kiwoom API call: {tr_code} → {data.get('stk_cd', 'Unknown')}")
        response = requests.post(url, headers=headers, json=data)
        
        # Response status and header info
        print(f'Response Code: {response.status_code}')
        header_info = {key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}
        print(f'Response Header: {json.dumps(header_info, indent=2, ensure_ascii=False)}')
        
        if response.status_code == 200:
            result = response.json()
            
            # Check return code in response body
            return_code = result.get('return_code', 0)
            if return_code == 0:
                print('✅ Kiwoom API call successful')
                
                # Response data size info
                response_size = len(json.dumps(result, ensure_ascii=False))
                print(f'Response data size: {response_size:,} bytes')
            else:
                return_msg = result.get('return_msg', 'Unknown error')
                print(f'⚠️  API returned error: [{return_code}] {return_msg}')
            
            return result
        else:
            print(f'❌ Kiwoom API call failed: HTTP {response.status_code}')
            print(f'Response content: {response.text}')
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return None


# Legacy function for backward compatibility
def make_api_request(token: str, tr_code: str, data: Dict) -> Optional[Dict]:
    """Legacy function - use make_api_request_with_retry instead"""
    return _make_single_api_request(token, tr_code, data)


# Chart data fetching functions with automatic token refresh
def get_minute_chart(stock_code: str, minute_scope: str) -> Optional[Dict]:
    """Get minute chart data (ka10080) with automatic token refresh"""
    data = {
        'stk_cd': stock_code,
        'tic_scope': minute_scope,
        'upd_stkpc_tp': '1'
    }
    return make_api_request_with_retry('ka10080', data)


def get_day_chart(stock_code: str, base_date: str) -> Optional[Dict]:
    """Get daily chart data (ka10081) with automatic token refresh"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request_with_retry('ka10081', data)


def get_week_chart(stock_code: str, base_date: str) -> Optional[Dict]:
    """Get weekly chart data (ka10082) with automatic token refresh"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request_with_retry('ka10082', data)


def get_month_chart(stock_code: str, base_date: str) -> Optional[Dict]:
    """Get monthly chart data (ka10083) with automatic token refresh"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request_with_retry('ka10083', data)


def get_year_chart(stock_code: str, base_date: str) -> Optional[Dict]:
    """Get yearly chart data (ka10094) with automatic token refresh"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request_with_retry('ka10094', data)


# Legacy functions for backward compatibility
def get_minute_chart_legacy(token: str, stock_code: str, minute_scope: str) -> Optional[Dict]:
    """Legacy function - use get_minute_chart instead"""
    data = {
        'stk_cd': stock_code,
        'tic_scope': minute_scope,
        'upd_stkpc_tp': '1'
    }
    return make_api_request(token, 'ka10080', data)


def get_day_chart_legacy(token: str, stock_code: str, base_date: str) -> Optional[Dict]:
    """Legacy function - use get_day_chart instead"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request(token, 'ka10081', data)


def get_week_chart_legacy(token: str, stock_code: str, base_date: str) -> Optional[Dict]:
    """Legacy function - use get_week_chart instead"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request(token, 'ka10082', data)


def get_month_chart_legacy(token: str, stock_code: str, base_date: str) -> Optional[Dict]:
    """Legacy function - use get_month_chart instead"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request(token, 'ka10083', data)


def get_year_chart_legacy(token: str, stock_code: str, base_date: str) -> Optional[Dict]:
    """Legacy function - use get_year_chart instead"""
    data = {
        'stk_cd': stock_code,
        'base_dt': base_date,
        'upd_stkpc_tp': '1'
    }
    return make_api_request(token, 'ka10094', data)


# Global token manager instance
_token_manager = None

def get_token_manager() -> KiwoomTokenManager:
    """Get global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = KiwoomTokenManager()
    return _token_manager 