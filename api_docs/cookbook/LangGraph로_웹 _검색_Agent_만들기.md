## 들어가며

---

AI 에이전트 기술은 단순한 대화형 모델을 넘어, 외부 도구(Tool)를 활용하여 필요한 정보를 직접 찾아 응답하는 방식으로 빠르게 진화하고 있습니다. 특히, 모델 단독으로는 한계가 있는 실시간 정보 검색과 같은 작업을 효과적으로 지원하기 위해, 검색 API를 연동한 '웹 검색 AI 에이전트'가 큰 주목을 받고 있습니다.

이 Cookbook에서는 LangGraph를 활용하여 검색 API를 도구로 사용하는 AI 에이전트 시스템을 단계별로 구축하는 과정을 상세히 안내합니다. 본 가이드를 따라 차근차근 실습하며 여러분만의 강력하고 맞춤화된 웹 검색 에이전트를 개발해 보세요.

## **Agent System 작동 원리**

---

웹 검색 AI 에이전트의 작동 방식을 먼저 살펴보겠습니다. 에이전트시스템은 사용자의 질문을 입력받아 그 의도를 파악하고, 필요시 가장 적절한 도구(Tool)를 선택하여 실행하는 방식으로 작동합니다. 여러 도구 중 현재 상황에 가장 적합한 것을 선택하여 사용하고, 얻어진 결과를 바탕으로 AI 모델이 자연스러운 언어로 정리하여 사용자에게 최종 응답을 제공합니다. 예를 들어, 사용자가 "오늘 서울 날씨 알려줘"라고 질문하면, 에이전트는 검색 API를 호출하여 최신 날씨 정보를 가져온 뒤, 이를 바탕으로 자연스러운 답변을 생성하는 원리입니다.

> **Tool**: AI 모델이 자체적으로 수행하기 어려운 기능(예: 웹 검색, 데이터 조회 등)을 함수나 API 형태로 호출하여 모델의 능력을 확장하는 수단입니다. (예: 검색 API)
> **Agent**: 사용자의 질문 의도를 파악하고, 필요한 도구(Function)를 판단하여 실행한 뒤, 그 결과를 종합하여 자연스러운 언어로 응답을 생성하는 핵심 제어 시스템입니다. (예: "실시간 날씨 정보 검색이 필요하겠군." → Tool 호출)
> **ChatClovaX**: AI 모델로서, 도구로부터 얻은 정보를 바탕으로 자연스러운 문장 형태의 답변을 재구성하여 사용자에게 전달하는 역할을 합니다.

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.3267f43409060c432d544b9e98db90b9.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.3267f43409060c432d544b9e98db90b9.png "Enlarge image")

## LangGraph AI Agent 구현 시작하기

---

이제 LangGraph를 이용하여 Tool을 연동한 AI 에이전트를 직접 구현해 보겠습니다. 검색 API를 도구로 활용하면, LLM이 자체 지식만으로는 답변하기 어려운 질문에 대해서도 더욱 정확하고 신뢰도 높은 답변을 제공할 수 있습니다.

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.17cb22203a19ae1e43a57a2e96056674.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.17cb22203a19ae1e43a57a2e96056674.png "Enlarge image")

### ① 기본 환경 설정

> **버전 정보**
> Python >= 3.13.2, langchain >= 0.3.23
> 본 쿡북은 Jupyter Notebook(.ipynb) 환경 기준으로 설계되어, 셀 단위로 코드 실행하고 결과를 확인할 수 있습니다.

**필요한 패키지 라이브러리 설치**
LangChain은 AI 에이전트 구축에 필요한 다양한 기능을 손쉽게 활용할 수 있게 해주는 파이썬 오픈소스 라이브러리입니다. 먼저 pip 명령어를 사용해 필요한 패키지들을 설치해보겠습니다.

```bash
%pip install -U langchain langchain-openai langchain-naver langgraph langchain-community langchain-naver-community
```

**CLOVA Studio API KEY 발급**
네이버 클라우드 플랫폼에서 CLOVA Studio 이용 신청을 해야 합니다. 이용 신청이 완료되면, CLOVA Studio 사이트에 로그인해 API 키를 발급받을 수 있습니다.

* 클로바 스튜디오 이용 신청: [https://www.ncloud.com/product/aiService/clovaStudio](https://www.ncloud.com/product/aiService/clovaStudio)
* 사용 가이드: [https://guide.ncloud-docs.com/docs/clovastudio-overview](https://guide.ncloud-docs.com/docs/clovastudio-overview)
* API 가이드: [https://api.ncloud-docs.com/docs/ai-naver-clovastudio-summary](https://api.ncloud-docs.com/docs/ai-naver-clovastudio-summary)

API 키는 CLOVA Studio에 로그인한 뒤, '프로필 > API 키 > 테스트 > 테스트 앱 발급' 경로를 통해 발급할 수 있습니다. 단, API 키는 한 번만 확인할 수 있으므로, 발급 직후 반드시 복사하여 별도로 안전하게 보관해두어야 합니다.

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.54dec46e0d45dbf32c5c1982c3d3a0a3.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.54dec46e0d45dbf32c5c1982c3d3a0a3.png "Enlarge image")

**CLOVA Studio 환경 변수 설정**
HCX-005 모델을 사용하기 위해, CLOVA Studio API 키를 환경 변수로 등록합니다. 아래 셀을 실행하면 API 키 입력란이 표시됩니다. 사이트에서 발급받은 API 키를 입력하여 환경 변수로 설정해 주세요.

```python
import os
import getpass

os.environ["CLOVASTUDIO_API_KEY"] = getpass.getpass("CLOVA Studio API Key 입력: ")
```

### ② LLM 모델 구현

**HCX 모델 정의**
Langchain-naver ChatClovaX를 통해 HCX-005 모델을 초기화합니다.

> **주의사항**
> 검색 API 등 Tool을 함께 사용하는 경우, 모델 파라미터 중 max\_tokens를 반드시 1024 이상으로 설정해야 합니다.

```python
from langchain_naver import ChatClovaX

llm = ChatClovaX(
    model="HCX-005",
    max_tokens=1024,  # Tool 사용시 max_tokens은 1024이상 필수
)
```

**HCX 모델 테스트**
모델 초기화 이후, "안녕, 너는 누구야?"와 같은 입력으로 간단한 테스트를 진행해 정상 작동 여부를 확인할 수 있습니다.

```python
llm.invoke("안녕,너는 누구야?")
```

```plaintext
AIMessage(content='안녕하세요! 저는 CLOVA X입니다.

사용자님의 생산성 향상을 도울 수 있도록 개발된 인공지능 언어모델로 다음과 같은 역할을 수행할 수 있습니다.

1. 질의 응답: 사용자님이 궁금하신 내용을 질문해 주시면, 이에 대해 학습한 데이터를 기반으로 최대한 정확하고 유용한 답변을 제공하도록 노력합니다.
2. 글쓰기 지원: 이메일 작성이나 문서 초안을 잡을 때 필요한 아이디어를 제시하거나 문장을 다듬어 드릴 수 있습니다.
3. 번역: 다양한 언어로 텍스트를 번역하는 데 도움을 줄 수 있습니다.
4. 요약 및 분석: 원문을 간략하게 요약하거나 특정 주제와 관련된 콘텐츠를 분석하여 인사이트를 제공합니다.

궁금하신 내용이나 도움이 필요하시면 언제든지 말씀해 주세요. 최선을 다해 도와드리겠습니다.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 164, 'prompt_tokens': 13, 'total_tokens': 177, 'completion_tokens_details': None, 'prompt_tokens_details': None}, 'model_name': 'HCX-005', 'system_fingerprint': None, 'id': '1b6d8c4819b04e70bde29e40d7d2068a', 'finish_reason': 'stop', 'logprobs': None}, id='run-b74541be-2b13-4c4b-b31f-40385f929ec2-0', usage_metadata={'input_tokens': 13, 'output_tokens': 164, 'total_tokens': 177, 'input_token_details': {}, 'output_token_details': {}})
```

### ③ Tool 구현

**검색 도구(Tool) API 이용신청**
검색 API를 사용하려면 먼저 [Tavily](https://tavily.com)에서 API 키를 발급받아야 합니다. Tavily 웹사이트에 로그인하면 아래 이미지와 같이 API 키가 자동으로 발급됩니다. 발급된 키는 오른쪽 복사 버튼(빨간색 박스)을 클릭해 안전하게 저장해두세요.

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.7cbc378b2c336b9b049913d4aeaabd64.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.7cbc378b2c336b9b049913d4aeaabd64.png "Enlarge image")

**다양한 검색 API 도구**
본 Cookbook에서는 Tavily API를 도구(Tool)로 사용하지만, 이 외에도 DuckDuckGo, Brave, Jina 등 다양한 무료 검색 API가 존재합니다. 각 검색 API의 특징과 사용 조건은 아래 표를 참고해 주세요.

| Tool/Toolkit                                                                         | Free/Paid                    | Return Data                                           |
| ------------------------------------------------------------------------------------ | ---------------------------- | ----------------------------------------------------- |
| [Bing Search](https://python.langchain.com/docs/integrations/tools/bing_search/)     | Paid                         | URL, Snippet, Title                                   |
| [Brave Search](https://python.langchain.com/docs/integrations/tools/brave_search/)   | Free                         | URL, Snippet, Title                                   |
| [DuckDuckgoSearch](https://python.langchain.com/docs/integrations/tools/ddg/)        | Free                         | URL, Snippet, Title                                   |
| [Exa Search](https://python.langchain.com/docs/integrations/tools/exa_search/)       | 1000 free searches/month     | URL, Author, Title, Published Date                    |
| [Google Search](https://python.langchain.com/docs/integrations/tools/google_search/) | Paid                         | URL, Snippet, Title                                   |
| [Google Serper](https://python.langchain.com/docs/integrations/tools/google_serper/) | Free                         | URL, Snippet, Title, Search Rank, Site Links          |
| [Jina Search](https://python.langchain.com/docs/integrations/tools/jina_search/)     | 1M Response Tokens Free      | URL, Snippet, Title, Page Content                     |
| [Mojeek Search](https://python.langchain.com/docs/integrations/tools/mojeek_search/) | Paid                         | URL, Snippet, Title                                   |
| [SearchApi](https://python.langchain.com/docs/integrations/tools/searchapi/)         | 100 Free Searches on Sign Up | URL, Snippet, Title, Search Rank, Site Links, Authors |
| [SearxNG Search](https://python.langchain.com/docs/integrations/tools/searx_search/) | Free                         | URL, Snippet, Title, Category                         |
| [SerpAPI](https://python.langchain.com/docs/integrations/tools/serpapi/)             | 100 Free Searches/Month      | Answer                                                |
| [Tavily Search](https://python.langchain.com/docs/integrations/tools/tavily_search/) | 1000 free searches/month     | URL, Content, Title, Images, Answer                   |
| [You.com Search](https://python.langchain.com/docs/integrations/tools/you/)          | Free for 60 days             | URL, Title, Page Content                              |

**검색 도구(Tool) 환경 변수 설정**
검색 도구를 사용하기 위해서는 API KEY가 필요합니다. API KEY를 환경 변수에 등록하여, 안전하고 편리하게 이용할 수 있습니다.

```python
os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API Key 입력: ")
```

**검색 도구 정의**
LangChain에서 제공하는 검색 도구를 불러와 `tool`이라는 이름으로 함수 객체를 정의합니다. 이때 `max_results` 파라미터를 사용해 최대 검색 결과 수를 지정할 수 있습니다.

```python
from langchain_community.tools.tavily_search import TavilySearchResults

tool = TavilySearchResults(max_results=5)
```

**검색 도구 테스트**
테스트 검색 도구가 정상적으로 동작하는지 확인하려면, `tool.invoke()` 함수를 실행합니다.

```python
tool.invoke("정자역")
```

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.fed8bb4c36192ce2d2fa11852fb86d31.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.fed8bb4c36192ce2d2fa11852fb86d31.png "Enlarge image")

**Agent 도구 정의**
Agent가 활용할 수 있는 도구는 자유롭게 정의할 수 있습니다. Tavily 검색 API 외에도 다양한 외부 API나 커스텀 함수를 함께 등록할 수 있으며, 모델은 상황에 따라 가장 적절한 도구를 자동으로 선택해 호출합니다. 이를 통해 보다 정밀하고 신뢰도 높은 응답을 생성할 수 있습니다. 아래 예시는 Tavily 외에 현재 시간을 반환하는 함수를 추가 도구로 구성한 사례입니다.

```python
tools = [tool]

# tools = [tool1, tool2, tool3, etc... ]
```

**여러 도구(Tool) 설정 방법**

```python
from datetime import datetime
from langchain_core.tools import Tool

def get_current_time(dummy: str = "now") -> dict:
    print("[tool2 호출] 현재 시간 조회\n")
    """현재 시간을 ISO 8601 형식으로 반환합니다."""
    return {"current_time": datetime.now().isoformat()}

tool2 = Tool.from_function(
    func=get_current_time,
    name="get_current_time",
    description="사용자가 현재 시간을 ISO 8601 포맷으로 반환합니다. 입력은 무시됩니다."
)

tools = [tool1, tool2]
```

### ④ Agent Workflow 구축

**LangGraph Agent 구현**
`langgraph.prebuilt` 라이브러리의 `create_react_agent` 함수를 사용하면, 간단한 코드 한 줄로 에이전트를 정의할 수 있습니다. 이 함수는 LangGraph에서 미리 정의한 REACT 기반 에이전트를 손쉽게 활용할 수 있도록 제공되는 강력한 모듈입니다. LLM 파라미터에는 앞서 정의한 언어 모델을, tools 파라미터에는 구성한 도구 목록을 각각 전달하여 설정합니다.

```python
from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(
    llm,
    tools,
)
```

**Agent 실행 함수 정의**
사용자의 입력을 받아 Agent Executor에 전달하고, 처리된 최종 응답 결과를 반환합니다.

```python
def agent_run(query):
    result = agent_executor.invoke({"messages": [("human", query)]})
    return result["messages"][-1].content
```

**에이전트 시스템 실행**
`while True` 루프를 사용하여 앞서 정의한 `agent_run` 함수를 반복 호출합니다. 이를 통해 에이전트 시스템이 사용자의 입력을 지속적으로 받아 처리할 수 있도록 구성합니다. 대화를 종료하려면 `quit`, `exit`, 또는 `q`를 입력하면 루프가 종료됩니다.

```python
while True:
    query = input("User: ")
    print("User: " + query + "\n")

    if query.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break

    print("Assistant: " + agent_run(query))
```

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.8bb7f15d755569a714ecbd99bc72182f.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.8bb7f15d755569a714ecbd99bc72182f.png "Enlarge image")

**랭그래프 Agent Workflow 시각화**
에이전트의 워크플로우 구조는 Mermaid 형식의 다이어그램을 통해 시각적으로 확인할 수 있습니다.

```python
from IPython.display import Image, display

display(Image(agent_executor.get_graph().draw_mermaid_png()))
```

[![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.17cb22203a19ae1e43a57a2e96056674.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.17cb22203a19ae1e43a57a2e96056674.png "Enlarge image")

**GUI로 쉽게 나만의 커스텀 Agentic Workflow 구현**
[LangGraph Builder](https://build.langchain.com) 는 초보자도 쉽게 워크플로우를 GUI로 구성할 수 있도록 지원하는 도구입니다. 시각적으로 구현한 워크플로우는 버튼 클릭 한 번으로 Python 또는 TypeScript 코드로 변환할 수 있습니다.

> **LangGraph Builder 시나리오**
> 아래 이미지와 같이, LangGraph Builder를 사용하면 Agentic Workflow를 GUI 환경에서 손쉽게 구성할 수 있습니다.
> [![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.f75efc9943a774245fdd7ec85cd2f6b8.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.f75efc9943a774245fdd7ec85cd2f6b8.png "Enlarge image")

> **LangGraph Builder 명령어**
>
> * **노드 생성:** ⌘ + 캔버스 아무 곳이나 클릭
> * **엣지(연결선) 생성:** 한 노드의 아래쪽에서 다른 노드의 위쪽으로 클릭 후 드래그
> * **조건부 엣지 생성:** 하나의 노드를 여러 노드에 연결
> * **사이클 생성:** 노드의 아래쪽에서 위쪽으로 클릭 후 드래그
> * **엣지/노드 삭제:** 엣지 또는 노드를 클릭하고 백스페이스 키 누르기
> * **엣지 색상 지정:** 엣지를 클릭한 후 색상 선택기에서 옵션 선택

> 기본 제공되는 Templates(템플릿) 버튼을 통해, 간단한 RAG 파이프라인이나 Agent with Tool 구성을 바로 불러와 활용할 수 있습니다.
> [![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.2f9a12593813053b3c863388c06617aa.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.2f9a12593813053b3c863388c06617aa.png "Enlarge image")

> 마지막으로, 우측 상단의 'Generate Code' 버튼을 클릭하면, GUI로 구성한 워크플로우를 Python 또는 TypeScript 코드로 손쉽게 변환하여 다운로드할 수 있습니다.
> [![Unavailable](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.d02291b9782eca19ecb941f61d18e030.png)](https://www.ncloud-forums.com/uploads/monthly_2025_05/image.png.d02291b9782eca19ecb941f61d18e030.png "Enlarge image")

# 마무리

---

이번 Cookbook에서는 LangGraph와 LangChain-naver를 활용하여 웹 검색 AI 에이전트를 구축하는 전 과정을 단계별로 살펴보았습니다. LangGraph와 Clova Studio, 다양한 검색 Tool을 조합하면, 실시간 정보를 이해하고 응답할 수 있는 강력한 AI Agent를 누구나 구현할 수 있습니다.

이제 여러분의 아이디어와 상상력이 더해질 차례입니다. 🚀