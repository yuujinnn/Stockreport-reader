# Stockreport-reader

**미래에셋증권 AI 페스티벌** |  AI Service 부문 [🔗](https://miraeassetfesta.com/)

---

## Stock Price 에이전트

키움증권 REST API를 사용하여 차트 데이터를 조회합니다.

```mermaid
sequenceDiagram
    participant U as 사용자
    participant A as StockPriceAgent
    participant L as LangChain Executor
    participant T as WeekChartTool
    participant TM as TokenManager
    participant K as 키움 API

    U->>A: "377300의 지난 1분기 주봉 데이터"
    A->>L: Agent 실행
    L->>T: get_week_chart(377300, "20250331")
    T->>TM: get_token_manager().get_access_token()
    TM->>TM: 토큰 유효성 검사
    alt 토큰 유효
        TM->>T: 기존 토큰 반환
    else 토큰 무효/만료
        TM->>K: 새 토큰 발급
        K->>TM: 새 토큰
        TM->>T: 새 토큰 반환
    end
    T->>K: fn_ka10082(token, ...)
    K->>T: 차트 데이터
    T->>L: JSON 응답
    L->>A: 결과
    A->>U: 분석된 답변
```
