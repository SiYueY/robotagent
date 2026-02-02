from langchain_text_splitters.base import TextSplitter as BaseTextSplitter
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)

_SUPPORTED_SPLIT_STRATEGY = [
    "recursive_character",
    "character"
]

class TextSplitter:
    def __init__(self, split_strategy: str):
        self.split_strategy = split_strategy
        self.splitter = self._get_text_splitter(split_strategy)
    
    def _get_text_splitter(self, split_strategy: str):
        if split_strategy not in _SUPPORTED_SPLIT_STRATEGY:
            suppoorted_split_strategy = ", ".join(_SUPPORTED_SPLIT_STRATEGY)
            msg = (
                f"Unsupported split strategy: {self.split_strategy}.\n"
                f"Supported split strategys: {suppoorted_split_strategy}."
            )
            raise ValueError(msg)
            
        if split_strategy in ["recursive_character"]:
            return RecursiveCharacterTextSplitter()
        elif split_strategy in ["character"]:
            return CharacterTextSplitter()
        else:
            suppoorted_split_strategy = ", ".join(_SUPPORTED_SPLIT_STRATEGY)
            msg = (
                f"Unsupported split strategy: {self.split_strategy}.\n"
                f"Supported split strategys: {suppoorted_split_strategy}."
            )
            raise ValueError(msg)

    def support_split_strategy(self) -> list[str]:
        return _SUPPORTED_SPLIT_STRATEGY
    
    def split_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)
    