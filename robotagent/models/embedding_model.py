from typing import Any

from langchain.embeddings import init_embeddings
from langchain.embeddings import Embeddings as EmbeddingModel

def create_embedding_model(
        model: str,
        provider: str | None = None,
        **kwargs: Any,
) -> EmbeddingModel:
    return init_embeddings(
        model=model,
        provider=provider,
        **kwargs
    )
