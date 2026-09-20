import chromadb
from typing import Optional
from app.core.config import settings
from app.core.dashscope_embedding import DashScopeEmbeddingFunction

class ChromaClient:
    def __init__(self):

        self.client = chromadb.PersistentClient(path="./chroma_db")

        self.dashscope_ef = DashScopeEmbeddingFunction(
            api_key=settings.DASHSCOPE_API_KEY,
            model_name="text-embedding-v1"
        )

        self.collection = self.client.get_or_create_collection(
            name="xuetuan_kb",
            metadata={"hnsw:space": "cosine"},  
            embedding_function=self.dashscope_ef
        )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_documents(self, query_text: str, user_id: Optional[int] = None, group_id: Optional[int] = None, n_results: int = 5):

        where_filter = {}
        if group_id:
            where_filter = {"group_id": group_id}
        elif user_id:
            where_filter = {"user_id": user_id}

        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )

    def delete_documents(self, ids: list[str]):

        self.collection.delete(ids=ids)

chroma_client = ChromaClient()