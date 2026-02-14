from os import PathLike
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional, Self, Sequence, Union

from langchain_community.document_loaders import (
    BSHTMLLoader,
    CSVLoader,
    JSONLoader,
)
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document


class DocumentLoader:
    def __init__(
        self,
        loader: BaseLoader,
    ) -> None:
        self._loader: BaseLoader = loader

    @classmethod
    def from_csv(
        cls,
        file_path: Union[str, Path],
        source_column: Optional[str] = None,
        metadata_columns: Sequence[str] = (),
        csv_args: Optional[Dict] = None,
        encoding: Optional[str] = None,
        autodetect_encoding: bool = False,
        *,
        content_columns: Sequence[str] = (),
    ) -> Self:
        loader = CSVLoader(
            file_path=file_path,
            source_column=source_column,
            metadata_columns=metadata_columns,
            csv_args=csv_args,
            encoding=encoding,
            autodetect_encoding=autodetect_encoding,
            content_columns=content_columns,
        )
        return cls(loader)

    @classmethod
    def from_json(
        cls,
        file_path: Union[str, PathLike],
        jq_schema: str,
        content_key: Optional[str] = None,
        is_content_key_jq_parsable: Optional[bool] = False,
        metadata_func: Optional[Callable[[Dict, Dict], Dict]] = None,
        text_content: bool = True,
        json_lines: bool = False,
    ) -> Self:
        loader = JSONLoader(
            file_path=file_path,
            jq_schema=jq_schema,
            content_key=content_key,
            is_content_key_jq_parsable=is_content_key_jq_parsable,
            metadata_func=metadata_func,
            text_content=text_content,
            json_lines=json_lines,
        )
        return cls(loader)

    @classmethod
    def from_html(
        cls,
        file_path: Union[str, Path],
        open_encoding: Union[str, None] = None,
        bs_kwargs: Union[dict, None] = None,
        get_text_separator: str = "",
    ) -> Self:
        loader = BSHTMLLoader(
            file_path=file_path,
            open_encoding=open_encoding,
            bs_kwargs=bs_kwargs,
            get_text_separator=get_text_separator,
        )
        return cls(loader)

    def load(self) -> list[Document]:
        try:
            docs: list[Document] = self._loader.load()
        except Exception as e:
            msg = f"Failed to load document: {e}"
            raise RuntimeError(msg) from e
        return docs

    def lazy_load(self) -> Iterator[Document]:
        try:
            docs: Iterator[Document] = self._loader.lazy_load()
        except Exception as e:
            msg = f"Failed to load document: {e}"
            raise RuntimeError(msg) from e
        return docs
