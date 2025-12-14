"""Text chunking utilities for RAG pipeline."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


class TextChunker:
    """
    Text chunker using recursive character splitting.

    Similar to LangChain's RecursiveCharacterTextSplitter but simplified.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: Optional[List[str]] = None,
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to try, in order of preference
        """
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
        self.separators = separators or [
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentence ends
            "! ",
            "? ",
            "; ",
            ", ",    # Clause breaks
            " ",     # Word breaks
            "",      # Character level (last resort)
        ]

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        chunks = []
        chunk_index = 0
        start_char = 0

        # Split recursively
        splits = self._split_text(text, self.separators)

        current_chunk = []
        current_length = 0

        for split in splits:
            split_length = len(split)

            # If adding this split would exceed chunk size
            if current_length + split_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "".join(current_chunk).strip()
                if chunk_text:
                    end_char = start_char + len(chunk_text)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        start_char=start_char,
                        end_char=end_char,
                        metadata=metadata.copy(),
                    ))
                    chunk_index += 1

                    # Calculate overlap start position
                    overlap_start = max(0, len(chunk_text) - self.chunk_overlap)
                    start_char = start_char + overlap_start

                # Start new chunk with overlap
                overlap_text = chunk_text[overlap_start:] if current_chunk else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)

            current_chunk.append(split)
            current_length += split_length

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "".join(current_chunk).strip()
            if chunk_text:
                end_char = start_char + len(chunk_text)
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char,
                    metadata=metadata.copy(),
                ))

        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using separators.

        Args:
            text: Text to split
            separators: List of separators to try

        Returns:
            List of text segments
        """
        if not separators:
            # No more separators, return character-level splits
            return list(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Empty separator means split by character
            return list(text)

        # Split by current separator
        splits = text.split(separator)

        result = []
        for i, split in enumerate(splits):
            if not split:
                continue

            # Check if this split is small enough
            if len(split) <= self.chunk_size:
                # Add separator back (except for last split)
                if i < len(splits) - 1:
                    result.append(split + separator)
                else:
                    result.append(split)
            else:
                # Need to split further
                sub_splits = self._split_text(split, remaining_separators)
                # Add separator to last sub-split if not last main split
                if i < len(splits) - 1 and sub_splits:
                    sub_splits[-1] = sub_splits[-1] + separator
                result.extend(sub_splits)

        return result

    def chunk_document_pages(
        self,
        pages: List[Dict[str, Any]],
        document_id: str,
        filename: str,
    ) -> List[TextChunk]:
        """
        Chunk a multi-page document, preserving page information.

        Args:
            pages: List of dicts with 'page_number' and 'text'
            document_id: Document ID for metadata
            filename: Filename for metadata

        Returns:
            List of TextChunk objects with page metadata
        """
        all_chunks = []
        global_chunk_index = 0

        for page in pages:
            page_number = page.get("page_number", 1)
            text = page.get("text", "")

            if not text.strip():
                continue

            metadata = {
                "document_id": document_id,
                "filename": filename,
                "page_number": page_number,
            }

            chunks = self.chunk_text(text, metadata)

            # Update global chunk index
            for chunk in chunks:
                chunk.chunk_index = global_chunk_index
                chunk.metadata["global_chunk_index"] = global_chunk_index
                global_chunk_index += 1

            all_chunks.extend(chunks)

        return all_chunks

    def estimate_chunk_count(self, text: str) -> int:
        """
        Estimate the number of chunks that will be created.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0

        text_length = len(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap

        if effective_chunk_size <= 0:
            return 1

        return max(1, (text_length + effective_chunk_size - 1) // effective_chunk_size)
