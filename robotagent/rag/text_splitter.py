from typing import Any, Literal, Self

from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_text_splitters.base import TextSplitter as BaseTextSplitter


class TextSplitter:
    def __init__(self, text_splitter: BaseTextSplitter):
        self._text_splitter: BaseTextSplitter = text_splitter

    @classmethod
    def from_recursive_character(
        cls,
        separators: list[str] | None = None,
        keep_separator: bool | Literal["start", "end"] = True,
        is_separator_regex: bool = False,
        **kwargs: Any,
    ) -> Self:
        splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            keep_separator=keep_separator,
            is_separator_regex=is_separator_regex,
            kwargs=kwargs,
        )
        return cls(splitter)

    @classmethod
    def from_character(
        cls,
        separator: str = "\n\n",
        is_separator_regex: bool = False,
        **kwargs: Any,
    ) -> Self:
        splitter = CharacterTextSplitter(
            separator=separator,
            is_separator_regex=is_separator_regex,
            kwargs=kwargs,
        )
        return splitter
