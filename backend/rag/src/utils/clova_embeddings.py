# clova_embeddings.py
from typing import List
from langchain.embeddings.base import Embeddings
from openai import OpenAI

class ClovaEmbeddings(Embeddings):
    def __init__(self, model_name: str, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://clovastudio.stream.ntruss.com/v1/openai"
        )
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
