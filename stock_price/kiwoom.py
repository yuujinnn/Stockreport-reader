"""
키움 REST API 차트 조회 함수들
"""
import requests
import json
from typing import Dict, Optional

# 기본 설정
BASE_URL_MOCK = 'https://mockapi.kiwoom.com'
BASE_URL_REAL = 'https://api.kiwoom.com'
CHART_ENDPOINT = '/api/dostk/chart'

def _make_request(token: str, tr_code: str, data: Dict) -> Optional[Dict]:
    """
    키움 API 요청을 수행하는 공통 함수 (문서 스펙 준수)
    
    Args:
        token (str): 접근토큰
        tr_code (str): TR 코드 (api-id)
        data (Dict): 요청 데이터
    
    Returns:
        Dict: API 응답 데이터
    """
    host = BASE_URL_REAL
    url = host + CHART_ENDPOINT
    
    # 문서에 명시된 정확한 헤더 구조
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': tr_code,
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # 응답 상태 코드와 헤더 정보 출력
        print('Code:', response.status_code)
        header_info = {key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}
        print('Header:', json.dumps(header_info, indent=4, ensure_ascii=False))
        
        # 응답 본문 출력
        result = response.json()
        print('Body:', json.dumps(result, indent=4, ensure_ascii=False))
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        return None

# ========== 주식 차트 조회 함수들 ==========

def fn_ka10079(token: str, stk_cd: str, tic_scope: str) -> Optional[Dict]:
    """
    주식틱차트조회요청 (ka10079)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        tic_scope (str): 틱범위 (1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자)
        - tic_scope: 틱범위 (String, 필수, 2자) - 1, 3, 5, 10, 30
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드
        - last_tic_cnt: 마지막틱갯수
        - stk_tic_chart_qry: 주식틱차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량  
          └ cntr_tm: 체결시간
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
    Returns:
        Dict: API 응답 데이터
    """
    # 틱범위 값 검증
    valid_tic_scopes = ['1', '3', '5', '10', '30']
    if tic_scope not in valid_tic_scopes:
        raise ValueError(f"tic_scope는 {valid_tic_scopes} 중 하나여야 합니다. 입력값: {tic_scope}")
    
    # ka10079 전용 body 파라미터 (API 가이드 스펙 준수)
    data = {
        'stk_cd': stk_cd,          # 종목코드 (거래소별 형식)
        'tic_scope': tic_scope,    # 틱범위 (1, 3, 5, 10, 30)
        'upd_stkpc_tp': '1'        # 수정주가 고정
    }
    return _make_request(token, 'ka10079', data)

def fn_ka10080(token: str, stk_cd: str, tic_scope: str) -> Optional[Dict]:
    """
    주식분봉차트조회요청 (ka10080)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        tic_scope (str): 틱범위 (1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자) - 거래소별 종목코드
        - tic_scope: 틱범위 (String, 필수, 2자) - 1, 3, 5, 10, 15, 30, 45, 60
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드 (String, 6자)
        - stk_min_pole_chart_qry: 주식분봉차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량
          └ cntr_tm: 체결시간
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분 (1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
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
    주식일봉차트조회요청 (ka10081)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자) - 거래소별 종목코드
        - base_dt: 기준일자 (String, 필수, 8자) - YYYYMMDD
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드 (String, 6자)
        - stk_dt_pole_chart_qry: 주식일봉차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량
          └ trde_prica: 거래대금
          └ dt: 일자
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분 (1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
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
    주식주봉차트조회요청 (ka10082)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자) - 거래소별 종목코드
        - base_dt: 기준일자 (String, 필수, 8자) - YYYYMMDD
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드 (String, 6자)
        - stk_stk_pole_chart_qry: 주식주봉차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량
          └ trde_prica: 거래대금
          └ dt: 일자
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분 (1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
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
    주식월봉차트조회요청 (ka10083)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자) - 거래소별 종목코드
        - base_dt: 기준일자 (String, 필수, 8자) - YYYYMMDD
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드 (String, 6자)
        - stk_mth_pole_chart_qry: 주식월봉차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량
          └ trde_prica: 거래대금
          └ dt: 일자
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분 (1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
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
    주식년봉차트조회요청 (ka10094)
    
    Args:
        token (str): 접근토큰
        stk_cd (str): 종목코드 (거래소별 종목코드 - KRX:039490, NXT:039490_NX, SOR:039490_AL)
        base_dt (str): 기준일자 (YYYYMMDD)
    
    Request Body:
        - stk_cd: 종목코드 (String, 필수, 20자) - 거래소별 종목코드
        - base_dt: 기준일자 (String, 필수, 8자) - YYYYMMDD
        - upd_stkpc_tp: 수정주가구분 (String, 필수, 1자) - 1 (수정주가 고정)
    
    Response Body:
        - stk_cd: 종목코드 (String, 6자)
        - stk_yr_pole_chart_qry: 주식년봉차트조회 리스트
          └ cur_prc: 현재가
          └ trde_qty: 거래량
          └ trde_prica: 거래대금
          └ dt: 일자
          └ open_pric: 시가
          └ high_pric: 고가
          └ low_pric: 저가
          └ upd_stkpc_tp: 수정주가구분 (1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
          └ upd_rt: 수정비율
          └ bic_inds_tp: 대업종구분
          └ sm_inds_tp: 소업종구분
          └ stk_infr: 종목정보
          └ upd_stkpc_event: 수정주가이벤트
          └ pred_close_pric: 전일종가
    
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


# ========== 편의 함수들 ==========

def save_chart_data_to_json(data: Dict, filename: str):
    """차트 데이터를 JSON 파일로 저장합니다"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"데이터가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 오류: {e}")

def get_today_date() -> str:
    """오늘 날짜를 YYYYMMDD 형식으로 반환합니다"""
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d') 