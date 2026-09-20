import dashscope
from typing import List
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from app.core.config import settings
from http import HTTPStatus

class DashScopeEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str = None, model_name: str = "text-embedding-v1"):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.model_name = model_name
        if not self.api_key:

            pass 
        if self.api_key:
            dashscope.api_key = self.api_key

    def __call__(self, input: Documents) -> Embeddings:
        if not self.api_key:
             raise ValueError("DASHSCOPE_API_KEY 未设置")

        batch_size = 25
        all_embeddings = []

        for i in range(0, len(input), batch_size):
            batch_input = input[i : i + batch_size]
            resp = dashscope.TextEmbedding.call(
                model=self.model_name,
                input=batch_input
            )

            if resp.status_code == HTTPStatus.OK:

                embeddings_data = resp.output['embeddings']

                sorted_embeddings = sorted(embeddings_data, key=lambda x: x['text_index'])
                batch_embeddings = [item['embedding'] for item in sorted_embeddings]
                all_embeddings.extend(batch_embeddings)
            else:
                raise Exception(f"调用 DashScope Embedding 失败: {resp.code}, {resp.message}")

        return all_embeddings