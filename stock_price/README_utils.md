# TokenManager 설정 및 사용 가이드

## 개요

`TokenManager`는 키움 REST API의 OAuth 토큰을 안전하게 관리하는 유틸리티입니다.

## 설정 방법

### 파일 기반 설정

```
secrets/
├── 57295187_appkey.txt     # 앱키 저장
└── 57295187_secretkey.txt  # 시크릿키 저장
```

## 사용 예시

### 기본 사용법

```python
from stock_price.utils import get_token_manager

# 토큰 매니저 생성
token_manager = get_token_manager()

# 접근 토큰 획득 (자동 재발급)
token = token_manager.get_access_token()
if token:
    print("토큰 획득 성공")
else:
    print("토큰 획득 실패")
```

### 고급 사용법

```python
# 강제 재발급
token = token_manager.get_access_token(force_refresh=True)

# 토큰 폐기
success = token_manager.revoke_token()
if success:
    print("토큰 폐기 완료")

# 특정 토큰 폐기
success = token_manager.revoke_token("specific_token_string")
```

## 보안 기능

### 1. 파일 권한 관리
- `secrets/` 디렉토리: 700 (소유자만 접근)
- 토큰 파일: 600 (소유자만 읽기/쓰기)

### 2. 토큰 자동 관리
- 만료 1시간 전 자동 재발급
- 유효하지 않은 토큰 자동 감지
- 토큰 파일 무결성 검증

## 에러 처리

### 일반적인 에러와 해결방법

```python
try:
    token = token_manager.get_access_token()
except FileNotFoundError as e:
    print(f"설정 파일 누락: {e}")
    # secrets/ 폴더에 키 파일 생성 또는 환경변수 설정
    
except ValueError as e:
    print(f"설정 오류: {e}")
    # 키 파일이 비어있거나 잘못된 형식
    
except Exception as e:
    print(f"예상치 못한 오류: {e}")
```

### 네트워크 에러

```python
# 타임아웃 설정으로 해결
os.environ['API_TIMEOUT'] = '60'  # 60초로 증가
```

## 모니터링

### 토큰 상태 확인

```python
# 현재 저장된 토큰 정보 확인
token_data = token_manager._load_token_from_file()
if token_data:
    print(f"토큰 만료일: {token_data['expires_dt']}")
    is_valid = token_manager._is_token_valid(token_data)
    print(f"토큰 유효성: {is_valid}")
```

## 문제 해결

### 1. 토큰 발급 실패
- 앱키/시크릿키 확인
- 네트워크 연결 확인
- API 서버 상태 확인

### 2. 권한 오류 (Linux/Mac)
```bash
# secrets 디렉토리 권한 수정
chmod 700 secrets/
chmod 600 secrets/*
```

### 3. 토큰 파일 손상
```python
# 토큰 파일 삭제 후 재발급
import os
if os.path.exists("secrets/access_token.json"):
    os.remove("secrets/access_token.json")

token = token_manager.get_access_token(force_refresh=True)
```

## 새로운 기능: LLM 기반 날짜 파싱

### 개요
에이전트는 자연어 날짜 표현을 LLM이 스스로 판단하여 파싱합니다.

### 반환 형식
날짜 파싱 결과는 다음 중 하나의 형식으로 반환됩니다:
- `YYYYMMDD,YYYYMMDD`: 명확한 날짜 범위 (예: "20250119,20250119")
- `ALL`: 역대 모든 데이터 요청 (상장부터 현재까지)
- `NONE`: 날짜 언급 없음 (최근 데이터만)

### ALL/NONE 처리 방법
- **ALL**: 역대 전체 데이터
  - base_date: 현재 날짜 사용
  - 동작: validate_chart_data로 계속 추가 호출하여 모든 히스토리 수집
- **NONE**: 날짜 언급 없음
  - base_date: 현재 날짜 사용  
  - 동작: 최초 300개 레코드만 조회 (추가 호출 안함)

## 설정 체크리스트

- [ ] 앱키/시크릿키 설정 (파일 기반)
- [ ] secrets 디렉토리 권한 확인 (700)
- [ ] 네트워크 연결 확인
- [ ] 토큰 파일 무결성 확인
- [ ] OpenAI API 키 설정 확인 (LLM 날짜 파싱용)