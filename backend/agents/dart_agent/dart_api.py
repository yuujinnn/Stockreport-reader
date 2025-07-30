"""
Simplified Kiwoom API module for ChatClovaX agent
Handles authentication and chart data fetching only
"""
import os
import requests
from dotenv import load_dotenv
import pandas as pd
import zipfile
import io

load_dotenv("secrets/.env")
dart_api_key = os.getenv("DART_API_KEY")

if not dart_api_key:
    raise RuntimeError("환경변수 DART_API_KEY 가 설정되지 않았습니다.")

##########질문에 대해서 어떤 보고서 종류를 판단해야할지 알아서 판단해라 prompting하기. 그게 pblntf_detail_ty이다.

# dart API를 통해 특정 기업의 보고서를 가져오는 함수
# tr_code는 기업의 고유 코드, pblntf_detail_ty는 보고서 종류를 나타냅니다.
# 예를 들어, 'A001'은 사업보고서, 'A002'는 분기보고서 등을 의미합니다.
# 이 함수는 해당 기업의 보고서 리스트를 가져와서 DataFrame 형태로 반환합니다.
def get_dart_report_list(tr_code, pblntf_detail_ty):
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        'crtfc_key': dart_api_key,  # ✅ 여기에 바로 사용
        'corp_code': tr_code,
        'pblntf_detail_ty': pblntf_detail_ty,
        'bgn_de': '20000101'
    }

    response = requests.get(url, params=params)
    result = response.json()
    if result['status'] == '013':
        print(f"📭 {tr_code}: failed to get dart report")
        return None
    
    df_imsi = pd.DataFrame(result['list'])
    df = df_imsi[~df_imsi['rm'].str.contains('정', na=False)]
    return df.to_dict(orient="records") 


##################왠지 프롬프트에 각각 recept_no이 뭔지 다 넣어줘야할 것 같다. 설명, 그리고 recept_no의 경우는 내가 그 df_ismi에서 보고 rcept_no를 발견하면 그거에 맞게 불러오기다.
# rcept_no로 본문 가져와줌.
def get_dart_report_text(rcept_no):           
    # df = self.get_dart_report(name, dart_code)
    # if df.empty:
    #     raise ValueError("❌ 해당 기업의 보고서가 존재하지 않습니다.")
    # rcept_no = self.extract_closest_code(20250713, df)

    url = "https://opendart.fss.or.kr/api/document.xml"
    params = {
        'crtfc_key': dart_api_key,
        'rcept_no': rcept_no,
    }
    r = requests.get(url, params=params)

    try:
        zf = zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile:
        raise ValueError("❌ DART에서 받은 응답이 ZIP 파일이 아닙니다.")

    file_list = zf.namelist()
    if not file_list:
        raise ValueError("❌ ZIP 파일 내에 파일이 없습니다.")

    target_file = min(file_list, key=len)

    with zf.open(target_file) as file:
        file_bytes = file.read()
        for encoding in ['euc-kr', 'utf-8', 'ISO-8859-1', 'cp949']:
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue

    raise ValueError("❌ 텍스트 디코딩 실패 (인코딩 문제)")