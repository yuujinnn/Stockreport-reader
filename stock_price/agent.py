"""
주식 차트 데이터 조회 에이전트
LangChain + OpenAI Function Calling 기반
"""
import os
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage
from langchain.memory import ConversationBufferMemory

from .tools import CHART_TOOLS

# secrets/.env 파일에서 환경변수 로드
load_dotenv("secrets/.env")

# LangSmith 설정
def setup_langsmith():
    """LangSmith 추적을 설정합니다"""
    langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
    
    if langchain_api_key:
        # 환경변수에서 LangSmith 설정값들 로드
        langsmith_tracing = os.getenv('LANGSMITH_TRACING', 'true')
        langsmith_endpoint = os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
        langsmith_project = os.getenv('LANGSMITH_PROJECT', 'stock-price-agent')
        
        os.environ["LANGCHAIN_TRACING_V2"] = langsmith_tracing
        os.environ["LANGCHAIN_ENDPOINT"] = langsmith_endpoint
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        
        print("LangSmith 추적이 활성화되었습니다.")
        print(f"프로젝트: {langsmith_project}")
        print(f"엔드포인트: {langsmith_endpoint}")
        print(f"대시보드: https://smith.langchain.com/")
    else:
        print("LANGCHAIN_API_KEY가 설정되지 않았습니다. LangSmith 추적이 비활성화됩니다.")

# 초기화 시 LangSmith 설정
setup_langsmith()


class StockPriceAgent:
    """주식 차트 데이터 조회 에이전트"""
    
    def __init__(self, openai_api_key: str = None):
        """
        에이전트 초기화
        
        Args:
            openai_api_key: OpenAI API 키 (None이면 환경변수에서 가져옴)
        """
        if not openai_api_key:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 매개변수로 전달하세요.")
        
        # 모델명도 환경변수에서 로드 (기본값: gpt-4o-mini)
        model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        temperature = float(os.getenv('OPENAI_TEMPERATURE', '0'))
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=openai_api_key
        )
        
        # 프롬프트 템플릿 설정
        self.prompt = self._create_prompt()
        
        # 에이전트 생성
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=CHART_TOOLS,
            prompt=self.prompt
        )
        
        # 에이전트 실행기 설정값들도 환경변수에서 로드
        max_iterations = int(os.getenv('AGENT_MAX_ITERATIONS', '10'))
        verbose = os.getenv('AGENT_VERBOSE', 'true').lower() == 'true'
        
        # 에이전트 실행기 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=CHART_TOOLS,
            verbose=verbose,
            return_intermediate_steps=True,
            max_iterations=max_iterations
        )
        
        # 메모리 (대화 기록 저장)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """에이전트용 프롬프트 템플릿 생성"""
        system_message = """당신은 키움 REST API를 통해 한국 주식 차트 데이터를 수집하는 전문 데이터 수집 에이전트입니다.

## 역할
오케스트레이터로부터 구조화된 데이터 요청을 받아 키움 REST API를 통해 정확한 차트 데이터를 수집하고 반환합니다.

## 입력 형식
오케스트레이터로부터 다음과 같은 JSON 형식의 요청을 받습니다:

```json
{
  "tickers": ["377300.KS", "005930.KS"],
  "from": "20250101",     // 또는 "NONE", "ALL"
  "to": "20250331",       // 또는 "NONE", "ALL"  
  "interval": "AUTO"      // 또는 "D", "W", "M", "Y", "1", "5", "15", "30", "60"
}
```

## 티커 코드 처리
거래소별 종목코드 변환이 자동으로 처리됩니다:
- "005930.KS" (코스피) → "005930"
- "000660.KQ" (코스닥) → "000660_AL" 
- "039490.NX" (코넥스) → "039490_NX"
- "005930" (접미사 없음) → "005930" (기본 KRX)

## 날짜 처리 규칙
### from/to 조합별 처리
1. **명확한 날짜 범위**: from="20250101", to="20250331"
   - 지정된 기간의 데이터 수집
   - base_date는 to 날짜 사용
   
2. **ALL**: from="ALL" 또는 to="ALL"
   - 역대 전체 데이터 수집
   - base_date는 현재 날짜 사용
   - validate_chart_data로 계속 추가 호출하여 모든 히스토리 수집
   
3. **NONE**: from="NONE" 또는 to="NONE"
   - 최근 데이터만 수집 (약 300개 레코드)
   - base_date는 현재 날짜 사용
   - 추가 호출 없이 최초 데이터만 반환

## interval 처리 (스마트 차트 선택)

### interval="AUTO"인 경우 (Zero Shot 선택)
당신이 직접 판단하여 가장 적절한 차트 유형을 선택하세요:

**고려 요소:**
- **분석 기간**: 1일 vs 1개월 vs 1년 vs 전체 히스토리
- **분석 목적**: 단기 트레이딩 vs 중장기 투자 vs 트렌드 분석
- **데이터 밀도**: 너무 많거나 적지 않은 적절한 데이터 포인트 수
- **시장 특성**: 변동성이 높은 구간에서는 더 세밀한 차트가 필요할 수 있음

**사용 가능한 차트 유형:**
- **틱차트**: get_tick_chart (1, 3, 5, 10, 30틱) - 초단기 실시간 분석
- **분봉차트**: get_minute_chart (1, 3, 5, 10, 15, 30, 45, 60분) - 단기 트레이딩
- **일봉차트**: get_day_chart - 일반적인 중단기 분석
- **주봉차트**: get_week_chart - 중장기 트렌드 분석  
- **월봉차트**: get_month_chart - 장기 트렌드 분석
- **년봉차트**: get_year_chart - 매우 장기 히스토리 분석

**판단 예시:**
- 1-2일 기간 → 5분봉 또는 15분봉 (세밀한 움직임 관찰)
- 1주일 기간 → 30분봉 또는 60분봉 (적절한 데이터 밀도)
- 1-3개월 기간 → 일봉 (표준적인 선택)
- 6개월-2년 기간 → 주봉 (트렌드 파악에 적합)
- 3년 이상 기간 → 월봉 또는 년봉 (장기 패턴 분석)

**창의적 판단 권장**: 위 가이드라인은 참고용이며, 상황에 따라 다른 선택도 가능합니다.

### interval 명시적 지정
- "D": 일봉 (get_day_chart)
- "W": 주봉 (get_week_chart)  
- "M": 월봉 (get_month_chart)
- "Y": 년봉 (get_year_chart)
- "1", "5", "15", "30", "60": 분봉 (get_minute_chart)

## 데이터 수집 전략
1. **초기 수집**: 선택된 차트 유형으로 데이터 조회
2. **완전성 검증**: validate_chart_data 툴로 데이터 완전성 확인
3. **추가 수집**: 누락 데이터가 있으면 제안된 기준일자로 재호출
4. **완전성 확보**: 요청 범위의 모든 데이터가 수집될 때까지 반복

## 응답 형식
수집된 모든 차트 데이터를 JSON 형식으로 반환합니다. 여러 호출의 결과는 통합하여 제공합니다.

## 예시 처리 과정

### 예시 1: AUTO 모드 - 창의적 판단
```json
입력: {"tickers": ["005930.KS"], "from": "20240101", "to": "20240331", "interval": "AUTO"}
```

**당신의 판단 과정:**
"3개월 기간의 삼성전자 데이터... 분기별 실적 트렌드를 보려면 일봉이 적절하겠다. 하지만 3개월이면 약 60-70개 거래일이므로 데이터 포인트가 적절하다. 일봉으로 선택!"

1. **차트 선택**: 일봉 선택 (get_day_chart)
2. **데이터 수집**: get_day_chart(005930, "20240331")  
3. **검증**: validate_chart_data로 범위 확인
4. **추가 수집**: 필요시 더 이른 기준일자로 재호출

### 예시 2: 단기 집중 분석
```json
입력: {"tickers": ["377300.KS"], "from": "20250115", "to": "20250117", "interval": "AUTO"}
```

**당신의 판단 과정:**
"3일간의 카카오페이 움직임... 단기 변동성이 클 수 있고 세밀한 진입점을 보려면 15분봉이 좋을 것 같다."

1. **차트 선택**: 15분봉 선택 (get_minute_chart)
2. **데이터 수집**: get_minute_chart(377300, "15")

## 중요 원칙
- **창의적 사고**: 고정된 룰에 얽매이지 말고 상황에 맞는 최적의 선택을 하세요
- **데이터 완전성**: 누락 데이터가 있으면 반드시 추가 수집
- **사용자 의도 파악**: 요청의 맥락과 목적을 고려한 차트 선택
- **JSON 응답**: 최종 결과는 정제된 JSON 데이터로만 반환
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt
    
    def query(self, user_input: str) -> Dict:
        """
        사용자 질의 처리
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            Dict: 처리 결과
        """
        try:
            # LangSmith 실행 이름 설정 (시간과 질의 내용 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name_prefix = os.getenv('LANGSMITH_RUN_PREFIX', 'stock_query')
            run_name = f"{run_name_prefix}_{timestamp}"
            
            # 환경변수에 실행 이름 설정 (LangSmith에서 사용)
            if os.getenv('LANGCHAIN_API_KEY'):
                os.environ["LANGCHAIN_RUN_NAME"] = run_name
            
            # 에이전트 실행
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.memory.chat_memory.messages
            })
            
            # 메모리에 대화 저장
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result["output"])
            
            return {
                "success": True,
                "output": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "run_name": run_name if os.getenv('LANGCHAIN_API_KEY') else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"오류가 발생했습니다: {str(e)}"
            }
    
    def clear_memory(self):
        """대화 메모리 초기화"""
        self.memory.clear()


def create_stock_agent(openai_api_key: str = None) -> StockPriceAgent:
    """주식 차트 에이전트 팩토리 함수"""
    return StockPriceAgent(openai_api_key)


# 데이터 디렉토리 생성
def ensure_data_directory():
    """data 디렉토리가 없으면 생성"""
    import os
    # 데이터 디렉토리 경로도 환경변수에서 가져올 수 있도록
    data_dir = os.getenv('DATA_DIRECTORY', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"{data_dir} 디렉토리를 생성했습니다.")


# 초기화 시 데이터 디렉토리 생성
ensure_data_directory() 