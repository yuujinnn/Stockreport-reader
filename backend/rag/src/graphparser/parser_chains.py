from langchain_naver import ChatClovaX
from langchain_core.runnables import chain
from langchain_core.rate_limiters import InMemoryRateLimiter
from .models import MultiModal
from .state import GraphState


@chain
def extract_image_summary(data_batches):
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=2.0,      # 초당 최대 2개 요청
        check_every_n_seconds=0.1,   # 100ms마다 체크
        max_bucket_size=3,            # 최대 버스트 크기
    )
    
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
        rate_limiter=rate_limiter,  # Rate Limiter 적용
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

    # 이미지 파일로 부터 질의 (Rate Limit 방지를 위해 순차 처리)
    answers = []
    for img_path, sys_prompt, usr_prompt in zip(image_paths, system_prompts, user_prompts):
        try:
            answer = multimodal_llm.invoke(img_path, sys_prompt, usr_prompt, display_image=False)
            answers.append(answer)
        except Exception as e:
            print(f"Image processing failed for {img_path}: {e}")
            answers.append("")  # 빈 답변으로 대체
    
    return answers


@chain
def extract_table_summary(data_batches):
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=2.0,      # 초당 최대 2개 요청
        check_every_n_seconds=0.1,   # 100ms마다 체크
        max_bucket_size=3,            # 최대 버스트 크기
    )
    
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
        rate_limiter=rate_limiter,  # Rate Limiter 적용
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

    # 테이블 파일로 부터 질의 (Rate Limit 방지를 위해 순차 처리)
    answers = []
    for img_path, sys_prompt, usr_prompt in zip(image_paths, system_prompts, user_prompts):
        try:
            answer = multimodal_llm.invoke(img_path, sys_prompt, usr_prompt, display_image=False)
            answers.append(answer)
        except Exception as e:
            print(f"Table processing failed for {img_path}: {e}")
            answers.append("")  # 빈 답변으로 대체
    
    return answers


@chain
def table_markdown_extractor(data_batches):
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=1.0,      # 초당 최대 2개 요청
        check_every_n_seconds=0.1,   # 100ms마다 체크
        max_bucket_size=3,            # 최대 버스트 크기
    )
    
    # 객체 생성
    llm = ChatClovaX(
        model="HCX-005",  # ChatClovaX HCX-005 모델
        max_tokens=4096,  # 충분한 토큰 수
        temperature=0,    # 일관된 분석을 위한 낮은 창의성
        rate_limiter=rate_limiter,  # Rate Limiter 적용
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

    # 테이블 마크다운 변환 (Rate Limit 방지를 위해 순차 처리)
    answers = []
    for img_path, sys_prompt, usr_prompt in zip(image_paths, system_prompts, user_prompts):
        try:
            answer = multimodal_llm.invoke(img_path, sys_prompt, usr_prompt, display_image=False)
            answers.append(answer)
        except Exception as e:
            print(f"Table markdown extraction failed for {img_path}: {e}")
            answers.append("")  # 빈 답변으로 대체
    
    return answers
