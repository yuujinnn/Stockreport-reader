# clova_embeddings.py
from typing import List
from langchain.embeddings.base import Embeddings
from langchain_core.rate_limiters import InMemoryRateLimiter
from openai import OpenAI
import time

class ClovaEmbeddings(Embeddings):
    def __init__(self, model_name: str, api_key: str, rate_limiter=None):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://clovastudio.stream.ntruss.com/v1/openai"
        )
        self.model_name = model_name
        self.rate_limiter = rate_limiter or InMemoryRateLimiter(
            requests_per_second=2.0,      # 초당 최대 2개 요청
            check_every_n_seconds=0.1,   # 100ms마다 체크
            max_bucket_size=3,            # 최대 버스트 크기
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        # Rate Limiter 적용 - 요청 전에 대기
        if self.rate_limiter:
            self.rate_limiter.acquire()
        
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
