from langchain_naver import ChatClovaX

def get_dart_llm():
    return ChatClovaX(
        model="HCX-005",
        max_tokens=4096,
        temperature=0,
    )

_dart_supervisor_llm = None
def get_dart_supervisor_llm():
    global _dart_supervisor_llm
    if _dart_supervisor_llm is None:
        _dart_supervisor_llm = ChatClovaX(model="HCX-005", max_tokens=4096, temperature=0)
    return _dart_supervisor_llm