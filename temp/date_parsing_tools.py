"""
날짜 파싱 관련 툴들 (사용하지 않음 - 오케스트레이터에서 처리)
"""
from typing import Dict, Optional, List, Tuple
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import openai

# secrets/.env 파일에서 환경변수 로드
load_dotenv("secrets/.env")

class DateRecognitionInput(BaseModel):
    query_text: str = Field(description="자연어로 작성된 날짜 표현 (예: '지난 1분기', '최근 3개월', '2024년 1년간')")


# LLM 기반 날짜 파싱 함수
def _parse_date_with_llm(query_text: str) -> str:
    """LLM을 사용하여 자연어 날짜를 YYYYMMDD 형식으로 파싱"""
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        
        client = openai.OpenAI(api_key=openai_api_key)
        today = datetime.now()
        
        prompt = f"""
현재 날짜: {today.strftime('%Y년 %m월 %d일 (%A)')}

다음 자연어 날짜 표현을 분석하여 시작일과 종료일을 YYYYMMDD 형식으로 변환해주세요.

입력: "{query_text}"

규칙:
1. 명확한 날짜/기간이 있으면 "YYYYMMDD,YYYYMMDD" 형식으로 반환
2. 역대/전체/모든 히스토리 데이터를 요구하면 "ALL" 반환
3. 날짜 언급이 아예 없으면 "NONE" 반환
4. 단일 날짜(어제, 오늘, 내일 등)는 시작일과 종료일이 같음
5. 기간 표현(지난 3개월, 최근 1분기 등)은 시작일과 종료일 계산

예시:
- "어제" → "20250119,20250119"
- "지난 3개월" → "20241020,20250120"
- "2024년" → "20240101,20241231"
- "2024년 전체 데이터" → "20240101,20241231"
- "역대 모든 데이터" → "ALL"
- "전체 히스토리 보여줘" → "ALL"
- "주가 확인" → "NONE"
- "차트 분석해줘" → "NONE"

답변:
"""
        
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "당신은 날짜 파싱 전문가입니다. 정확한 YYYYMMDD,YYYYMMDD 형식으로만 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        
        # 결과 검증
        if result in ["ALL", "NONE"]:
            return result
        elif ',' in result and len(result.split(',')) == 2:
            start_date, end_date = result.split(',')
            # YYYYMMDD 형식 검증
            datetime.strptime(start_date, '%Y%m%d')
            datetime.strptime(end_date, '%Y%m%d')
            return result
        else:
            raise ValueError(f"잘못된 LLM 응답 형식: {result}")
            
    except Exception as e:
        print(f"LLM 날짜 파싱 실패: {e}")
        return None


class DateRecognitionTool(BaseTool):
    name = "parse_date_range"
    description = "자연어 날짜를 YYYYMMDD,YYYYMMDD/ALL/NONE으로 변환. ALL=역대전체, NONE=날짜언급없음"
    args_schema = DateRecognitionInput

    def _run(self, query_text: str) -> str:
        try:
            # LLM으로 날짜 파싱 시도
            llm_result = _parse_date_with_llm(query_text)
            
            if llm_result:
                return llm_result
            
            # LLM 실패 시 기본값으로 NONE 반환
            return "NONE"
            
        except Exception as e:
            # 에러 발생 시에도 NONE 반환
            return "NONE" 