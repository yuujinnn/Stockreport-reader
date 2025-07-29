# NewsAgent

네이버 뉴스 API를 활용한 뉴스 검색 및 분석 에이전트

## 🚀 기능

- **뉴스 검색**: 네이버 뉴스 API를 통한 관련 기사 검색
- **관련성 필터링**: ChatClovaX를 활용한 지능형 기사 선별
- **종합 분석**: 뉴스 동향 분석 및 인사이트 추출
- **구조화된 보고서**: 체계적인 뉴스 분석 리포트 생성

## 📋 환경 설정

### 1. 환경 변수 설정

`backend/secrets/.env` 파일을 생성하고 다음 API 키들을 설정하세요:

```bash
# CLOVA Studio API Key (ChatClovaX 용)
CLOVASTUDIO_API_KEY=your_clova_studio_api_key_here

# Naver News API Credentials (뉴스 검색 용)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

### 2. API 키 발급

#### CLOVA Studio API
1. [CLOVA Studio](https://clovastudio.naver.com/) 접속
2. 계정 생성 및 로그인
3. API 키 발급

#### Naver News API
1. [네이버 개발자센터](https://developers.naver.com/apps/) 접속
2. 애플리케이션 등록
3. 뉴스 검색 API 추가
4. Client ID 및 Client Secret 확인

## 🧪 테스트

```bash
# NewsAgent 테스트 실행
python backend/agents/news_agent/test.py
```

## 📖 사용법

### 직접 사용

```python
from backend.agents.news_agent import NewsAgent

agent = NewsAgent()
result = agent.run("카카오페이 굿딜서비스 관련 뉴스 분석")
print(result)
```

### Supervisor Agent를 통한 사용

```python
# Supervisor Agent가 자동으로 뉴스 관련 요청을 NewsAgent로 라우팅
query = "삼성전자 AI 반도체 사업 관련 최근 동향은?"
# Supervisor가 call_news_agent 도구 사용
```

## 🛠️ 도구 (Tools)

1. **search_news**: 네이버 뉴스 검색
2. **filter_news**: 관련성 기반 기사 필터링
3. **analyze_news**: 종합 뉴스 분석

## 🏗️ 아키텍처

- **LangGraph**: ReAct 패턴 기반 에이전트
- **ChatClovaX HCX-005**: 뉴스 분석 및 필터링
- **Naver News API**: 뉴스 데이터 소스
- **LangChain Tools**: 모듈화된 기능 구성

## 📊 출력 형식

```markdown
## 📰 [주제] 뉴스 분석 보고서

### 🔍 주요 발견사항
- 핵심 내용 1
- 핵심 내용 2

### 📊 동향 분석
[시장 동향 및 패턴 분석]

### 💡 주요 인사이트
[도출된 중요한 통찰]

### 📅 시간적 맥락
[뉴스의 최신성 및 흐름]

### 📖 참고 자료
[분석에 사용된 주요 뉴스 출처]

### ⚡ 핵심 결론
[명확한 결론]
``` 