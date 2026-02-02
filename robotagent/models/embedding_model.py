from typing import Any

from langchain.embeddings import init_embeddings, Embeddings


def create_embedding_model(
        model: str,
        provider: str | None = None,
        **kwargs: Any,
) -> Embeddings:
    return init_embeddings(
        model=model,
        provider=provider,
        **kwargs
    )
