# ── 0. install once ────────────────────────────────────────────────────────────
# %pip install -U langchain langchain-openai langgraph \
#             langchain-naver langchain-community langchain-naver-community
# ------------------------------------------------------------------------------

import os
from datetime import datetime
from langchain_naver import ChatClovaX          # Clova-aware wrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langsmith import Client

# ── 1. API keys (insert yours) ─────────────────────────────────────────────────
os.environ["CLOVASTUDIO_API_KEY"] = "nv-17d4138bceec4cf48235222d11b06046UJbv"
os.environ["TAVILY_API_KEY"]      = "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"   # search tool
os.environ["LANGCHAIN_TRACING_V2"] = "true"            # turn tracing on
os.environ["LANGCHAIN_API_KEY"]    = "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"
os.environ["LANGCHAIN_PROJECT"]    = "MiraeAssetAI"

# ── 2. LLM model (HCX-005) ─────────────────────────────────────────────────────
llm = ChatClovaX(
    model="HCX-005",
    max_tokens=4096,   # ≥1024 if tools are involved :contentReference[oaicite:0]{index=0}
)

# ── 3. Tools: Tavily search  +  a tiny “current time” helper ───────────────────
tool_search = TavilySearchResults(max_results=5)                # :contentReference[oaicite:1]{index=1}

def get_current_time(_: str = "now") -> dict:
    print("[tool2 호출] 현재 시간 조회\n")
    """Return current time in ISO-8601."""
    return datetime.now().isoformat()

tool_time = Tool.from_function(                                # :contentReference[oaicite:2]{index=2}
    func=get_current_time,
    name="get_current_time",
    description="현재 시간을 조회합니다. (format: YYYY-MM-DDTHH:MM:SS)"
)

tools = [tool_search, tool_time]

# ── 4. Build the REACT agent with LangGraph helper ─────────────────────────────
agent_executor = create_react_agent(                           # :contentReference[oaicite:3]{index=3}
    llm,
    tools,
)

# ── 5. Simple CLI loop ─────────────────────────────────────────────────────────
def main() -> None:
    print("Type your question (or 'q' to quit)…\n")
    while True:
        query = input("User: ").strip()
        if query.lower() in {"q", "quit", "exit"}:
            print("Goodbye!"); break

        result = agent_executor.invoke({"messages": [("human", query)]})
        print("Assistant:", result["messages"][-1].content, "\n")

if __name__ == "__main__":
    main()
