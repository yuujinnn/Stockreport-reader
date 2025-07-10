import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class TokenManager:
    def __init__(self):
        """
        토큰 매니저 초기화
        """
        self.base_url = "https://api.kiwoom.com"
        self.token_file = "secrets/access_token.json"
        
        # secrets 폴더에서 키 정보 로드
        self.appkey = self._load_secret("57295187_appkey.txt")
        self.secretkey = self._load_secret("57295187_secretkey.txt")
        
    def _load_secret(self, filename: str) -> str:
        """secrets 폴더에서 키 정보를 로드합니다"""
        try:
            with open(f"secrets/{filename}", "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"secrets/{filename} 파일을 찾을 수 없습니다.")
    
    def _save_token_to_file(self, token_data: Dict):
        """토큰을 파일에 저장합니다"""
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            print(f"토큰이 {self.token_file}에 저장되었습니다.")
        except Exception as e:
            print(f"토큰 저장 오류: {e}")
    
    def _load_token_from_file(self) -> Optional[Dict]:
        """파일에서 토큰을 로드합니다"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"토큰 로드 오류: {e}")
        return None
    
    def _is_token_valid(self, token_data: Dict) -> bool:
        """토큰이 유효한지 확인합니다"""
        if not token_data or 'expires_dt' not in token_data:
            return False
        
        try:
            expires_dt = datetime.strptime(token_data['expires_dt'], '%Y%m%d%H%M%S')
            # 만료 1시간 전에 재발급
            buffer_time = timedelta(hours=1)
            return datetime.now() < (expires_dt - buffer_time)
        except ValueError:
            return False
    
    def get_access_token(self, force_refresh=False) -> Optional[str]:
        """
        유효한 접근토큰을 반환합니다. 필요시 자동으로 재발급합니다.
        
        Args:
            force_refresh (bool): 강제 재발급 여부
            
        Returns:
            str: 유효한 접근토큰 또는 None
        """
        # 강제 재발급이 아닌 경우, 기존 토큰 확인
        if not force_refresh:
            existing_token = self._load_token_from_file()
            if existing_token and self._is_token_valid(existing_token):
                print("기존 토큰을 사용합니다.")
                return existing_token['token']
        
        # 새 토큰 발급
        print("새로운 접근토큰을 발급받습니다.")
        token_data = self._request_new_token()
        
        if token_data and token_data.get('return_code') == 0:
            # 토큰을 파일에 저장
            self._save_token_to_file(token_data)
            return token_data['token']
        
        return None
    
    def _request_new_token(self) -> Optional[Dict]:
        """새로운 접근토큰을 발급받습니다"""
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
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('return_code') == 0:
                print(f"접근토큰 발급 성공")
                print(f"토큰 만료일: {result['expires_dt']}")
                return result
            else:
                print(f"토큰 발급 실패: {result.get('return_msg')}")
                return result
                
        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """접근토큰을 폐기합니다"""
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
                print("토큰 폐기 성공")
                # 저장된 토큰 파일 삭제
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                return True
            else:
                print(f"토큰 폐기 실패: {result.get('return_msg')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            return False


class TickerManager:
    """
    티커 변환 및 관리 클래스
    """
    
    def __init__(self):
        """
        티커 매니저 초기화
        """
        # 거래소별 매핑 규칙
        self.exchange_mapping = {
            'KS': '',        # 코스피 (KRX) - 접미사 없음
            'KQ': '_AL',     # 코스닥 (SOR) - _AL 접미사
            'NX': '_NX',     # 코넥스 (KONEX) - _NX 접미사
        }
        
        # 지원하는 거래소 목록
        self.supported_exchanges = set(self.exchange_mapping.keys())
    
    def convert_to_kiwoom_format(self, ticker: str) -> str:
        """
        티커를 키움 API 형식의 종목코드로 변환합니다.
        
        Args:
            ticker: 티커 코드 (예: "377300.KS", "000660.KQ", "039490.NX", "005930")
            
        Returns:
            str: 키움 API 형식 종목코드
            
        Examples:
            - "005930.KS" → "005930" (코스피)
            - "000660.KQ" → "000660_AL" (코스닥)  
            - "039490.NX" → "039490_NX" (코넥스)
            - "005930" → "005930" (기본 KRX)
        """
        if '.' not in ticker:
            # 거래소 접미사가 없으면 기본 KRX 형식
            return ticker
        
        stock_code, exchange = ticker.split('.', 1)
        
        # 거래소 코드 매핑
        suffix = self.exchange_mapping.get(exchange.upper(), '')
        return f"{stock_code}{suffix}"
    
    def convert_multiple_tickers(self, tickers: List[str]) -> List[str]:
        """
        여러 티커를 키움 API 형식으로 변환합니다.
        
        Args:
            tickers: 티커 리스트 (예: ["005930.KS", "000660.KQ"])
            
        Returns:
            List[str]: 변환된 종목코드 리스트 (예: ["005930", "000660_AL"])
        """
        return [self.convert_to_kiwoom_format(ticker) for ticker in tickers]
    
    def get_exchange_info(self, ticker: str) -> Dict[str, str]:
        """
        티커에서 거래소 정보를 추출합니다.
        
        Args:
            ticker: 티커 코드 (예: "005930.KS")
            
        Returns:
            Dict: 거래소 정보 (exchange, exchange_name, kiwoom_format)
        """
        if '.' not in ticker:
            return {
                'exchange': 'KRX',
                'exchange_name': '한국거래소 (기본)',
                'kiwoom_format': ticker
            }
        
        stock_code, exchange = ticker.split('.', 1)
        exchange_upper = exchange.upper()
        
        exchange_names = {
            'KS': '코스피 (KOSPI)',
            'KQ': '코스닥 (KOSDAQ)', 
            'NX': '코넥스 (KONEX)'
        }
        
        return {
            'exchange': exchange_upper,
            'exchange_name': exchange_names.get(exchange_upper, f'알 수 없는 거래소 ({exchange})'),
            'kiwoom_format': self.convert_to_kiwoom_format(ticker)
        }
    
    def validate_ticker_format(self, ticker: str) -> bool:
        """
        티커 형식이 유효한지 검증합니다.
        
        Args:
            ticker: 티커 코드
            
        Returns:
            bool: 유효 여부
        """
        if not ticker:
            return False
        
        # 거래소 접미사가 없는 경우 (기본 KRX)
        if '.' not in ticker:
            return ticker.isdigit() and len(ticker) == 6
        
        # 거래소 접미사가 있는 경우
        parts = ticker.split('.')
        if len(parts) != 2:
            return False
        
        stock_code, exchange = parts
        
        # 종목코드는 6자리 숫자
        if not (stock_code.isdigit() and len(stock_code) == 6):
            return False
        
        # 지원하는 거래소인지 확인
        return exchange.upper() in self.supported_exchanges
    
    def get_supported_exchanges(self) -> Dict[str, str]:
        """
        지원하는 거래소 목록을 반환합니다.
        
        Returns:
            Dict: 거래소 코드와 이름 매핑
        """
        return {
            'KS': '코스피 (KOSPI)',
            'KQ': '코스닥 (KOSDAQ)',
            'NX': '코넥스 (KONEX)'
        }


def get_token_manager() -> TokenManager:
    """토큰 매니저 인스턴스를 반환합니다"""
    return TokenManager()


def get_ticker_manager() -> TickerManager:
    """티커 매니저 인스턴스를 반환합니다"""
    return TickerManager() 