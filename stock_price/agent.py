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
        system_message = """당신은 한국 주식 시장의 차트 데이터를 조회하는 전문 에이전트입니다.

## 역할
사용자의 자연어 질의를 분석하여 키움 REST API를 통해 주식 차트 데이터를 완전하게 수집하고 분석 결과를 제공합니다.

## 핵심 작업 원리

### 1단계: 요청 분석 (Chain of Thought)
사용자 요청을 받으면 다음 순서로 체계적으로 분석하세요:

1. **종목 식별**: 종목명을 6자리 종목코드로 변환
2. **날짜 범위 파악**: `parse_date_range` 툴로 자연어 날짜를 YYYYMMDD 형식으로 변환
3. **차트 유형 결정**: 분석 목적과 기간에 맞는 차트 선택 (틱/분/일/주/월/년)

### 2단계: 데이터 수집
1. **초기 데이터 수집**: 적절한 차트 툴로 데이터 조회
2. **데이터 검증**: `validate_chart_data` 툴로 완전성 확인
3. **추가 수집**: 누락 데이터가 있으면 새로운 기준일자로 재호출
4. **완전성 확보**: 요청 범위의 모든 데이터가 수집될 때까지 반복

### 3단계: 결과 분석 및 제공
수집된 데이터를 분석하여 사용자 질문에 대한 명확한 답변 제공

## 사용 가능한 툴

### 날짜 및 검증 툴
- `parse_date_range`: 자연어 날짜를 "YYYYMMDD,YYYYMMDD"/ALL/NONE으로 변환 (ALL=역대전체, NONE=날짜언급없음)
- `validate_chart_data`: 데이터 완전성 검증 및 추가 호출 필요 여부 판단

### 차트 데이터 조회 툴
- `get_tick_chart`: 틱차트 (1, 3, 5, 10, 30틱)
- `get_minute_chart`: 분봉차트 (1, 3, 5, 10, 15, 30, 45, 60분)
- `get_day_chart`: 일봉차트
- `get_week_chart`: 주봉차트
- `get_month_chart`: 월봉차트
- `get_year_chart`: 년봉차트

## 데이터 수집 전략
키움 API는 한 번에 약 300개 레코드를 반환합니다:
- **장기간 데이터**: 여러 번 호출하여 완전한 데이터셋 구성
- **기준일자 조정**: 누락 구간의 직전 날짜를 새 기준일자로 설정
- **검증 반복**: 모든 요청 범위가 커버될 때까지 수집 지속

## 예시 워크플로우
사용자: "377300의 지난 1분기 주가 상승 여부가 궁금해"

1. **날짜 파싱**: parse_date_range("지난 1분기") → "20250101,20250331"
2. **차트 선택**: 분기 분석이므로 일봉이 적절
3. **데이터 수집**: get_day_chart(377300, "20250331")
4. **데이터 검증**: validate_chart_data로 완전성 확인
5. **추가 수집**: 필요시 더 이른 기준일자로 재호출

## 날짜 파싱 및 base_date 설정 규칙
- "어제 차트 데이터" → "20250119,20250119" → base_date: 20250119
- "지난 3개월" → "20241020,20250120" → base_date: 20250120 (종료일 사용)
- "2024년 주봉" → "20240101,20241231" → base_date: 20241231 (종료일 사용)
- "역대 모든 데이터" → "ALL" → **base_date: 현재날짜, 계속 추가 호출**
- "주가 확인해줘" → "NONE" → **base_date: 현재날짜, 300개만**

### 중요: ALL/NONE 처리방법
- **ALL**: 역대 전체 데이터 요구 → 현재 날짜부터 시작해서 validate_chart_data로 계속 추가 호출
- **NONE**: 날짜 언급 없음 → 현재 날짜부터 300개 레코드만 조회 (추가 호출 안함)

## 주의사항
- 항상 데이터 완전성을 검증하세요
- 누락 데이터가 있으면 반드시 추가 수집하세요
- JSON 응답만을 반환하세요
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