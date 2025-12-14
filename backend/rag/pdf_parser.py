"""PDF parsing utilities for document ingestion."""

import io
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ParsedPage:
    """Represents a parsed page from a PDF."""
    page_number: int
    text: str
    metadata: Dict[str, Any]


@dataclass
class ParsedDocument:
    """Represents a fully parsed PDF document."""
    filename: str
    pages: List[ParsedPage]
    total_pages: int
    metadata: Dict[str, Any]

    @property
    def full_text(self) -> str:
        """Get all text from the document."""
        return "\n\n".join(page.text for page in self.pages)


class PDFParser:
    """Parser for extracting text from PDF files."""

    def __init__(self):
        """Initialize the PDF parser."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import pdfplumber
            self._use_pdfplumber = True
        except ImportError:
            self._use_pdfplumber = False

        try:
            import PyPDF2
            self._use_pypdf2 = True
        except ImportError:
            self._use_pypdf2 = False

        if not self._use_pdfplumber and not self._use_pypdf2:
            raise ImportError(
                "Either pdfplumber or PyPDF2 must be installed for PDF parsing. "
                "Install with: pip install pdfplumber or pip install PyPDF2"
            )

    def parse(
        self,
        file_content: bytes,
        filename: str,
        extract_metadata: bool = True,
    ) -> ParsedDocument:
        """
        Parse a PDF file and extract text from all pages.

        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            extract_metadata: Whether to extract PDF metadata

        Returns:
            ParsedDocument with all pages and metadata
        """
        if self._use_pdfplumber:
            return self._parse_with_pdfplumber(file_content, filename, extract_metadata)
        else:
            return self._parse_with_pypdf2(file_content, filename, extract_metadata)

    def _parse_with_pdfplumber(
        self,
        file_content: bytes,
        filename: str,
        extract_metadata: bool,
    ) -> ParsedDocument:
        """Parse PDF using pdfplumber (preferred)."""
        import pdfplumber

        pages = []
        metadata = {}

        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            if extract_metadata and pdf.metadata:
                metadata = {
                    k: v for k, v in pdf.metadata.items()
                    if v is not None and isinstance(v, (str, int, float))
                }

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                # Clean up text
                text = self._clean_text(text)

                pages.append(ParsedPage(
                    page_number=i + 1,
                    text=text,
                    metadata={
                        "width": page.width,
                        "height": page.height,
                    }
                ))

        return ParsedDocument(
            filename=filename,
            pages=pages,
            total_pages=len(pages),
            metadata=metadata,
        )

    def _parse_with_pypdf2(
        self,
        file_content: bytes,
        filename: str,
        extract_metadata: bool,
    ) -> ParsedDocument:
        """Parse PDF using PyPDF2 (fallback)."""
        import PyPDF2

        pages = []
        metadata = {}

        reader = PyPDF2.PdfReader(io.BytesIO(file_content))

        if extract_metadata and reader.metadata:
            metadata = {
                k.replace("/", ""): v
                for k, v in reader.metadata.items()
                if v is not None and isinstance(v, (str, int, float))
            }

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = self._clean_text(text)

            pages.append(ParsedPage(
                page_number=i + 1,
                text=text,
                metadata={}
            ))

        return ParsedDocument(
            filename=filename,
            pages=pages,
            total_pages=len(pages),
            metadata=metadata,
        )

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Remove null characters
        text = text.replace('\x00', '')

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def extract_text_by_page(
        self,
        file_content: bytes,
        filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract text from PDF, returning a list of page contents.

        Args:
            file_content: PDF file content as bytes
            filename: Original filename

        Returns:
            List of dicts with page_number, text, and char_count
        """
        parsed = self.parse(file_content, filename, extract_metadata=False)

        return [
            {
                "page_number": page.page_number,
                "text": page.text,
                "char_count": len(page.text),
            }
            for page in parsed.pages
        ]
