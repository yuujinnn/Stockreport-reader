"""
키움증권 REST API 함수들
Stock Price Agent 전용 구현 (legacy 코드 기반 완전한 토큰 관리)
"""

import os
import json
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv("secrets/.env")

# 키움증권 API 설정 (legacy 코드 기반)
BASE_URL_MOCK = 'https://mockapi.kiwoom.com'
BASE_URL_REAL = 'https://api.kiwoom.com'
CHART_ENDPOINT = '/api/dostk/chart'


class KiwoomTokenManager:
    """키움 API 토큰 관리자 (legacy utils.py 완전 구현)"""
    
    def __init__(self):
        """토큰 매니저 초기화"""
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
            print(f"✅ 토큰이 {self.token_file}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 토큰 저장 오류: {e}")
    
    def _load_token_from_file(self) -> Optional[Dict]:
        """파일에서 토큰을 로드합니다"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ 토큰 로드 오류: {e}")
        return None
    
    def _is_token_valid(self, token_data: Dict) -> bool:
        """토큰이 유효한지 확인합니다"""
        if not token_data or 'expires_dt' not in token_data:
            return False
        
        try:
            expires_dt = datetime.strptime(token_data['expires_dt'], '%Y%m%d%H%M%S')
            # 만료 1시간 전에 재발급
            buffer_time = timedelta(hours=1)
            current_time = datetime.now()
            
            is_valid = current_time < (expires_dt - buffer_time)
            
            if is_valid:
                remaining = expires_dt - current_time
                print(f"🔑 토큰 유효: {remaining.total_seconds()/3600:.1f}시간 남음")
            else:
                print(f"⏰ 토큰 만료 임박 또는 만료됨")
                
            return is_valid
        except ValueError as e:
            print(f"❌ 토큰 만료일 파싱 오류: {e}")
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
                print("✅ 기존 토큰을 사용합니다.")
                return existing_token['token']
        
        # 새 토큰 발급
        print("🔄 새로운 접근토큰을 발급받습니다...")
        token_data = self._request_new_token()
        
        if token_data and token_data.get('return_code') == 0:
            # 토큰을 파일에 저장
            self._save_token_to_file(token_data)
            print("✅ 새 토큰 발급 및 저장 완료")
            return token_data['token']
        else:
            print(f"❌ 토큰 발급 실패: {token_data.get('return_msg', 'Unknown error') if token_data else 'API 호출 실패'}")
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
            print(f"🌐 토큰 요청: {url}")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('return_code') == 0:
                expires_dt = result.get('expires_dt', '')
                print(f"✅ 접근토큰 발급 성공")
                print(f"📅 토큰 만료일: {expires_dt}")
                return result
            else:
                print(f"❌ 토큰 발급 실패: {result.get('return_msg')}")
                return result
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
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
                print("✅ 토큰 폐기 성공")
                # 저장된 토큰 파일 삭제
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                return True
            else:
                print(f"❌ 토큰 폐기 실패: {result.get('return_msg')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            return False


# 전역 매니저 인스턴스
_token_manager = None

def get_token_manager() -> KiwoomTokenManager:
    """전역 토큰 매니저 인스턴스 반환"""
    global _token_manager
    if _token_manager is None:
        _token_manager = KiwoomTokenManager()
    return _token_manager


def _make_request(token: str, tr_code: str, data: Dict) -> Optional[Dict]:
    """
    키움 API 요청을 수행하는 공통 함수 (legacy 코드 기반 문서 스펙 준수)
    
    Args:
        token (str): 접근토큰
        tr_code (str): TR 코드 (api-id)
        data (Dict): 요청 데이터
    
    Returns:
        Dict: API 응답 데이터
    """
    host = BASE_URL_REAL
    url = host + CHART_ENDPOINT
    
    # 문서에 명시된 정확한 헤더 구조 (legacy 코드 기반)
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': tr_code,
    }
    
    try:
        print(f"🌐 키움 API 호출: {tr_code} → {data.get('stk_cd', 'Unknown')}")
        response = requests.post(url, headers=headers, json=data)
        
        # 응답 상태 코드와 헤더 정보 출력 (legacy 코드 스타일)
        print(f'📊 응답 Code: {response.status_code}')
        header_info = {key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}
        print(f'📋 응답 Header: {json.dumps(header_info, indent=2, ensure_ascii=False)}')
        
        if response.status_code == 200:
            result = response.json()
            print('✅ 키움 API 호출 성공')
            
            # 응답 데이터 크기 정보
            response_size = len(json.dumps(result, ensure_ascii=False))
            print(f'📦 응답 데이터 크기: {response_size:,} bytes')
            
            return result
        else:
            print(f'❌ 키움 API 호출 실패: HTTP {response.status_code}')
            print(f'📄 응답 내용: {response.text}')
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 오류: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return None


# ========== 주식 차트 조회 함수들 (legacy 코드 기반) ==========

def fn_ka10079(token: str, stk_cd: str, tic_scope: str) -> Optional[Dict]:
    """
    주식틱차트조회요청 (ka10079) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        tic_scope (str): 틱범위 (1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱)
    
    Returns:
        Dict: API 응답 데이터
    """
    # 틱범위 값 검증
    valid_tic_scopes = ['1', '3', '5', '10', '30']
    if tic_scope not in valid_tic_scopes:
        raise ValueError(f"tic_scope는 {valid_tic_scopes} 중 하나여야 합니다. 입력값: {tic_scope}")
    
    # ka10079 전용 body 파라미터 (API 가이드 스펙 준수)
    data = {
        'stk_cd': stk_cd,          # 종목코드
        'tic_scope': tic_scope,    # 틱범위 (1, 3, 5, 10, 30)
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10079', data)

def fn_ka10080(token: str, stk_cd: str, tic_scope: str) -> Optional[Dict]:
    """
    주식분봉차트조회요청 (ka10080) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        tic_scope (str): 틱범위 (1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분)
    
    Returns:
        Dict: API 응답 데이터
    """
    # ka10080 전용 body 파라미터
    data = {
        'stk_cd': stk_cd,
        'tic_scope': tic_scope,
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10080', data)

def fn_ka10081(token: str, stk_cd: str, base_dt: str) -> Optional[Dict]:
    """
    주식일봉차트조회요청 (ka10081) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Returns:
        Dict: API 응답 데이터
    """
    # ka10081 전용 body 파라미터
    data = {
        'stk_cd': stk_cd,
        'base_dt': base_dt,
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10081', data)

def fn_ka10082(token: str, stk_cd: str, base_dt: str) -> Optional[Dict]:
    """
    주식주봉차트조회요청 (ka10082) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Returns:
        Dict: API 응답 데이터
    """
    # ka10082 전용 body 파라미터
    data = {
        'stk_cd': stk_cd,
        'base_dt': base_dt,
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10082', data)

def fn_ka10083(token: str, stk_cd: str, base_dt: str) -> Optional[Dict]:
    """
    주식월봉차트조회요청 (ka10083) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Returns:
        Dict: API 응답 데이터
    """
    # ka10083 전용 body 파라미터
    data = {
        'stk_cd': stk_cd,
        'base_dt': base_dt,
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10083', data)

def fn_ka10094(token: str, stk_cd: str, base_dt: str) -> Optional[Dict]:
    """
    주식년봉차트조회요청 (ka10094) - legacy 코드 기반
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Returns:
        Dict: API 응답 데이터
    """
    # ka10094 전용 body 파라미터
    data = {
        'stk_cd': stk_cd,
        'base_dt': base_dt,
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10094', data)


# ========== 편의 함수들 (legacy 코드 기반) ==========

def save_chart_data_to_json(data: Dict, filename: str):
    """차트 데이터를 JSON 파일로 저장합니다"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 데이터가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 파일 저장 오류: {e}")

def get_today_date() -> str:
    """오늘 날짜를 YYYYMMDD 형식으로 반환합니다"""
    return datetime.now().strftime('%Y%m%d') 