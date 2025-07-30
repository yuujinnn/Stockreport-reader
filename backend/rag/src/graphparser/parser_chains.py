from langchain_naver import ChatClovaX
from langchain_core.runnables import chain
from .models import MultiModal
from .state import GraphState


@chain
def extract_image_summary(data_batches):
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
    )

    system_prompt = """You are an expert in extracting useful information from IMAGE.
With a given image, your task is to extract key entities, summarize them, and write useful information that can be used later for retrieval.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["image"]
        language = data_batch["language"]
        user_prompt_template = f"""Here is the context related to the image: {context}
        
###

Output Format:

제목:
[title]
요약:
[summary]
핵심어:
[entities]

Output must be written in {language}.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer


@chain
def extract_table_summary(data_batches):
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
    )

    system_prompt = """You are an expert in extracting useful information from TABLE. 
With a given image, your task is to extract key entities, summarize them, and write useful information that can be used later for retrieval.
If the numbers are present, summarize important insights from the numbers.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["table"]
        language = data_batch["language"]
        user_prompt_template = f"""Here is the context related to the image of table: {context}
        
###

Output Format:

제목:
[title]
요약:
[summary]
핵심 인사이트: 
[data_insights]

Output must be written in {language}.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer


@chain
def table_markdown_extractor(data_batches):
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
    )

    system_prompt = "You are an expert in converting image of the TABLE into markdown format. Be sure to include all the information in the table. DO NOT narrate, just answer in markdown format."

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        image_path = data_batch["table"]
        user_prompt_template = f"""DO NOT wrap your answer in ```markdown``` or any XML tags.
        
###

Output Format:

<table_markdown>

Output must be written in Korean.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer
