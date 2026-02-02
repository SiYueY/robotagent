from pathlib import Path
from typing import Iterator

from langchain_community.document_loaders import (
    CSVLoader,
    JSONLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document


_SUPPORTED_FILE_TYPES = [
    ".csv",
    ".json",
    ".pdf",
    ".txt",
    ".html",
    ".md",
    ".docx",
]

class DocumentLoader:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_type = Path(file_path).suffix.lower()
        self.loader = self._get_document_loader()

    def _get_document_loader(self) -> BaseLoader:
        if self.file_type not in _SUPPORTED_FILE_TYPES:
            supported_file_types = ", ".join(_SUPPORTED_FILE_TYPES)
            msg = (
                f"Unsupported file type: {self.file_type}.\n"
                f"Supported file types: {supported_file_types}."
            )
            raise ValueError(msg)

        if self.file_type in [".csv"]:
            return CSVLoader(self.file_path)
        elif self.file_type in [".json"]:
            return JSONLoader(self.file_path)
        elif self.file_type in [".pdf"]:
            return PyPDFLoader(self.file_path)
        elif self.file_type in [".txt"]:
            return TextLoader(self.file_path)
        elif self.file_type in [".html"]:
            return UnstructuredHTMLLoader(self.file_path)
        elif self.file_type in [".md"]:
            return UnstructuredMarkdownLoader(self.file_path)
        elif self.file_type in [".docx"]:
            return UnstructuredWordDocumentLoader(self.file_path)
        else:
            supported_file_types = ", ".join(_SUPPORTED_FILE_TYPES)
            msg = (
                f"Unsupported file type: {self.file_type}.\n"
                f"Supported file types: {supported_file_types}."
            )
            raise ValueError(msg)

    def load(self) -> list[Document]:
        return self.loader.load()

    def lazy_load(self) -> Iterator[Document]:
        return self.loader.lazy_load()
    
    def support_file_types(self) -> list[str]:
        return _SUPPORTED_FILE_TYPES
