from langchain_text_splitters.base import TextSplitter
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter
)

class DocumentSplitter:
    def __init__(self, splitter_type: str = "recursive_character"):
        self.splitter_type = splitter_type
        self.splitter = self._get_document_splitter(splitter_type)
    
    def _get_document_splitter(self, splitter_type: str):
        if splitter_type == "recursive_character":
            return RecursiveCharacterTextSplitter()
        elif splitter_type == "character":
            return CharacterTextSplitter()
        elif splitter_type == "markdown_header":
            return MarkdownHeaderTextSplitter()
        else:
            raise ValueError(f"Invalid splitter type: {splitter_type}")
    
    def split(self, text: str) -> list[str]:
        return self.splitter.split_text(text)