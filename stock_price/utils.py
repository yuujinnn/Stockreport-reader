"""
키움 REST API OAuth 토큰 관리 유틸리티
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

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

def get_token_manager() -> TokenManager:
    """토큰 매니저 인스턴스를 반환합니다"""
    return TokenManager() 