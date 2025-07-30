"""
Simplified LangChain tools for ChatClovaX agent
Returns pandas DataFrames with upgrade suggestions when needed
"""

from __future__ import annotations
from typing import List, Tuple

import json
import re
import difflib
from typing import Dict, List, Type

import pandas as pd
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from .clova_api import get_dart_llm
from .dart_api import get_dart_report_list, get_dart_report_text
from .prompt import DART_REPORT_TYPE_PROMPT, DART_SECTION_PROMPT
from pydantic import PrivateAttr
from typing import Any

##############여기 부터
# 입력 스키마 정의
class DartReportTypeInput(BaseModel):
    user_query: str


# Tool 클래스 정의
class DartReportTypeTool(BaseTool):
    llm: BaseLanguageModel
    prompt_template: str
    name: str = "get_dart_report_type_code"
    description: str = "사용자 질문을 기반으로 DART 보고서 코드 하나를 추론합니다."
    args_schema: Type[BaseModel] = DartReportTypeInput
    _agent: Any = PrivateAttr() 

    def __init__(self, llm: BaseLanguageModel, prompt_template: str):
        super().__init__(llm=llm, prompt_template=prompt_template)
        self.llm = llm
        self.prompt_template = prompt_template
        self._agent = create_react_agent(self.llm, tools=[], prompt=self.prompt_template)

    # noqa: D401 – LangChain 내부 규약
    def _run(self, user_query: str) -> str:  # type: ignore[override]
        structured_input = (
            "다음은 사용자의 질문입니다.\n"
            f"- 질문(query): {user_query}\n"
            "위 질문을 참고하여 필요한 **DART 보고서 코드**만 출력하세요."
        )
        result = self._agent.invoke({"messages": [HumanMessage(content=structured_input)]})
        return result["messages"][-1].content.strip()

# 입력값 스키마 정의
class DartReportListInput(BaseModel):
    tr_code: str
    pblntf_detail_ty: str

# Tool 클래스 정의
class DartReportListTool(BaseTool):
    name: str = "get_dart_report_list"
    description: str = "종목코드·보고서 유형으로 DART 보고서 목록(JSON) 반환"
    args_schema: Type[BaseModel] = DartReportListInput

    def _run(self, tr_code: str, pblntf_detail_ty: str) -> str:  # type: ignore[override]
        data = get_dart_report_list(tr_code, pblntf_detail_ty)
        return json.dumps(data, ensure_ascii=False)

class RceptNoByDateInput(BaseModel):
    target_date: int  # 예: 20240405
    report_list: List[Dict]  # rcept_dt 포함된 공시 JSON 리스트

class RceptNoByDateTool(BaseTool):
    name: str = "get_rcept_no_by_date"
    description: str = "report_list에서 입력 날짜 혹은 가장 인접한 날짜의 rcept_no를 반환"
    args_schema: Type[BaseModel] = RceptNoByDateInput

    def _run(self, target_date: int, report_list: List[Dict]) -> str:  # type: ignore[override]
        df = pd.DataFrame(report_list)
        if not {"rcept_dt", "rcept_no"}.issubset(df.columns):
            raise ValueError("report_list에 'rcept_dt' 또는 'rcept_no' 컬럼이 없습니다.")

        df["rcept_dt_int"] = df["rcept_dt"].astype(int)
        df["date_diff"] = (df["rcept_dt_int"] - target_date).abs()

        if target_date in df["rcept_dt_int"].values:
            row = df[df["rcept_dt_int"] == target_date].iloc[0]
            return row["rcept_no"]
        closest_row = df.loc[df["date_diff"].idxmin()]
        return closest_row["rcept_no"]


  
class ReportThenTitleListInput(BaseModel):
    rcept_no: str
        
class ExtractReportThenTitleListTool(BaseTool):
    name: str = "extract_report_then_title_list_from_xml"
    description: str = "rcept_no로 공시 XML 추출 후 <TITLE> 목록 추출"
    args_schema: Type[BaseModel] = ReportThenTitleListInput

    def _run(self, rcept_no: str) -> str:  # type: ignore[override]
        xml_text = get_dart_report_text(rcept_no) 
        title_list = re.findall(r"<TITLE[^>]*>(.*?)</TITLE>", xml_text, flags=re.DOTALL) #json.dumps(tags, ensure_ascii=False)
        return title_list 
    
    
# 입력 스키마 정의
class RecommendSectionInput(BaseModel):
    title_list : List[str]
    user_query: str
    # xml_text: str

# Tool 클래스 정의

class RecommendSectionTool(BaseTool):
    llm: BaseLanguageModel
    prompt_template: str
    _agent: Any = PrivateAttr()
    model_config = {"extra": "allow"}   # 임의 속성 허용

    name: str = "recommend_section_from_titles_list"
    description: str = "TITLE 리스트·질문을 바탕으로 참조 섹션 추천"
    args_schema: Type[BaseModel] = RecommendSectionInput
    
    def __init__(self, llm: BaseLanguageModel, prompt_template: str):
        super().__init__(llm=llm, prompt_template=prompt_template)
        self._agent = create_react_agent(self.llm, tools=[], prompt=self.prompt_template)

    def _run(self, title_list: List[str], user_query: str) -> List[str] :  #-> Dict[str, List[str]],  type: ignore[override]
        prompt_txt = self.prompt_template.format(user_query=user_query, title_list=title_list)
        raw = self._agent.invoke({"messages": [HumanMessage(content=prompt_txt)]})["messages"][-1].content.strip()
        
        # 코드펜스 제거(혹시 LLM이 ```json ...``` 감싸서 줄 때)
        raw = re.sub(r"```.*?```", "", raw, flags=re.S).strip()

        # ▶ ① 따옴표 제거 & 콤마 분리
        items = [
            part.strip().strip('"').strip("'")
            for part in raw.split(",")
            if part.strip()
        ]
        return items or [raw]
    


class ReportThenSectionTextInput(BaseModel):
    recommend_section: List[str] #Dict[str, List[str]]
    title_list: List[str]
    rcept_no: str
    #xml_text: str
    
class ExtractReportThenSectionTextTool(BaseTool):
    """추천 섹션의 본문을 원문 XML에서 추출하는 LangChain Tool"""

    name: str = "extract_report_then_section_text"
    description: str = "rcept_no와 목차 리스트, recommend_section을 기반으로 공시 XML을 추출 후 추천 섹션의 본문을 추출합니다."
    args_schema: Type[BaseModel] = ReportThenSectionTextInput
    
    @staticmethod
    def _extract_section_by_title(document_text: str, section_title: str) -> str:
        matches = list(re.finditer(r'<TITLE[^>]*>(.*?)</TITLE>', document_text, re.DOTALL | re.IGNORECASE))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            if section_title.lower() in title.lower():
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(document_text)
                body_raw = document_text[start:end]
                body_clean = re.sub(r'<[^>]+>', ' ', body_raw)
                body_clean = re.sub(r'\s+', ' ', body_clean).strip()
                return body_clean

        return f"❌ '{section_title}' 섹션을 찾을 수 없습니다."

    # ------------------------------ core ------------------------------ #
    # pylint: disable=too-many-locals
    def _run(
        self,
        recommend_section: List[str],
        title_list: List[str],
        rcept_no: str,
    ) -> str:
        xml_text = get_dart_report_text(rcept_no)

        # 추천 섹션 정리
        sections: List[str] = []
        for item in recommend_section:
            if not isinstance(item, str):
                continue
            item = item.strip().strip('"').strip("'")
            parts = [p.strip().strip('"').strip("'") for p in item.split(",") if p.strip()]
            sections.extend(parts or [item])

        results: List[str] = []

        for sec in sections:
            # title_list에서 가장 유사한 TITLE 찾기
            closest = difflib.get_close_matches(sec, title_list, n=1)
            ref_title = closest[0] if closest else sec
            print(f"🔍 추천 섹션: '{sec}' → 가장 유사한 title: '{ref_title}'")

            # 본문 추출
            section_body = self._extract_section_by_title(xml_text, ref_title)
            results.append(f"# {ref_title}\n{section_body}")

        return "\n\n".join(results)

def get_stock_tools():
    """Get list of stock-related tools"""
    dart_llm = get_dart_llm()
    return [
        DartReportTypeTool(llm = dart_llm, prompt_template = DART_REPORT_TYPE_PROMPT),
        DartReportListTool(),
        RceptNoByDateTool(),
        ExtractReportThenTitleListTool(),
        RecommendSectionTool(llm  = dart_llm, prompt_template= DART_SECTION_PROMPT),
        ExtractReportThenSectionTextTool(),
    ]
    
    