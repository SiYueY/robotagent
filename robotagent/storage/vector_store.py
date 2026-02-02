from typing import Any, Iterable

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore as BaseVectorStore
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_milvus import Milvus

from robotagent.models.embedding_model import EmbeddingModel

_SUPPORTED_VECTOR_STORE_TYPES = [
    "memory",
    "milvus",
]

class VectorStore:
    def __init__(self, vector_store_type: str):
        self.vector_store_type = vector_store_type
        self.store = self._get_vector_store(vector_store_type)

    def _get_vector_store(self, vector_store_type: str) -> BaseVectorStore:
        if vector_store_type not in _SUPPORTED_VECTOR_STORE_TYPES:
            supported_vector_store_types = ", ".join(_SUPPORTED_VECTOR_STORE_TYPES)
            msg = (
                f"Unsupported vector storage type: {vector_store_type}. "
                f"Supported types are: {supported_vector_store_types}"
            )
            raise ValueError(msg)

        if vector_store_type == "memory":
            return InMemoryVectorStore()
        elif vector_store_type == "milvus":
            return Milvus()
        else:
            supported_vector_store_types = ", ".join(_SUPPORTED_VECTOR_STORE_TYPES)
            msg = (
                f"Unsupported vector storage type: {vector_store_type}. "
                f"Supported types are: {supported_vector_store_types}"
            )
            raise ValueError(msg)

    def support_vector_store_types(self) -> list[str]:
        return _SUPPORTED_VECTOR_STORE_TYPES

    def embedding_model(self) -> EmbeddingModel | None:
        return self.store.embedding_model()

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        return self.store.add_texts(texts=texts, metadatas=metadatas, ids=ids, **kwargs)

    def add_documents(self, documents: list[Document], **kwargs: Any) -> list[str]:
        return self.store.add_documents(documents=documents, **kwargs)

    def delete(self, ids: list[str] | None = None, **kwargs: Any) -> bool | None:
        return self.store.delete(ids=ids, **kwargs)

    def similarity_search(
        self, query: str, k: int = 4, **kwargs: Any
    ) -> list[Document]:
        return self.store.similarity_search(query=query, k=k, **kwargs)
