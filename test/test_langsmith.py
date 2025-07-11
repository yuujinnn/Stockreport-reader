import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# secrets/.env 파일에서 환경변수 로드
load_dotenv("secrets/.env")

# .env에서 로드된 키들 확인
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
langsmith_project = os.getenv("LANGSMITH_PROJECT", "stock-price-agent")
langsmith_tracing = os.getenv("LANGSMITH_TRACING", "true")
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY가 secrets/.env 파일에 설정되지 않았습니다.")

print("LangSmith 설정 완료")
print(f"프로젝트: {langsmith_project}")
print(f"엔드포인트: {langsmith_endpoint}")
print(f"추적 활성화: {langsmith_tracing}")

# ChatOpenAI 모델 초기화 및 테스트
llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai_api_key)
response = llm.invoke("Hello, world!")

print("\nLangSmith 테스트 결과:")
print(f"응답: {response.content}")