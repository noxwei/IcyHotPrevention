"""Text chunking for embedding generation."""

from dataclasses import dataclass
from typing import Iterator, Optional
import hashlib
import logging

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    text: str
    index: int
    start_char: int
    end_char: int
    token_count: int
    content_hash: str


class TextChunker:
    """Chunks text into overlapping segments for embedding.

    Uses tiktoken for accurate token counting with the specified model.
    Default settings: 512 tokens max, 50 token overlap.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        encoding_name: str = "cl100k_base",
    ):
        """Initialize the chunker.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between chunks
            encoding_name: Tiktoken encoding name
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        return len(self.encoding.encode(text))

    def _compute_hash(self, text: str) -> str:
        """Compute content hash for deduplication.

        Args:
            text: Text to hash

        Returns:
            SHA-256 hash (first 16 chars)
        """
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def chunk_text(self, text: str) -> Iterator[TextChunk]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Yields:
            TextChunk instances
        """
        if not text or not text.strip():
            return

        # Encode entire text
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        if total_tokens <= self.max_tokens:
            # Text fits in single chunk
            yield TextChunk(
                text=text,
                index=0,
                start_char=0,
                end_char=len(text),
                token_count=total_tokens,
                content_hash=self._compute_hash(text),
            )
            return

        # Split into overlapping chunks
        chunk_index = 0
        token_start = 0

        while token_start < total_tokens:
            # Determine chunk end
            token_end = min(token_start + self.max_tokens, total_tokens)

            # Decode chunk tokens back to text
            chunk_tokens = tokens[token_start:token_end]
            chunk_text = self.encoding.decode(chunk_tokens)

            # Calculate character positions (approximate)
            # For accurate positions, we'd need to track during encoding
            char_start = len(self.encoding.decode(tokens[:token_start]))
            char_end = char_start + len(chunk_text)

            yield TextChunk(
                text=chunk_text,
                index=chunk_index,
                start_char=char_start,
                end_char=char_end,
                token_count=len(chunk_tokens),
                content_hash=self._compute_hash(chunk_text),
            )

            # Move to next chunk with overlap
            token_start = token_end - self.overlap_tokens
            chunk_index += 1

            # Prevent infinite loop if overlap >= max_tokens
            if token_start >= token_end:
                break

    def chunk_with_metadata(
        self,
        text: str,
        source_id: str,
        source_schema: str,
        source_table: str,
    ) -> Iterator[dict]:
        """Chunk text and attach source metadata.

        Args:
            text: Text to chunk
            source_id: ID of source record
            source_schema: Database schema name
            source_table: Database table name

        Yields:
            Dict with chunk data and metadata
        """
        for chunk in self.chunk_text(text):
            yield {
                "source_id": source_id,
                "source_schema": source_schema,
                "source_table": source_table,
                "chunk_index": chunk.index,
                "chunk_text": chunk.text,
                "token_count": chunk.token_count,
                "content_hash": chunk.content_hash,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }


class SentenceChunker:
    """Chunks text by sentences while respecting token limits.

    Attempts to keep sentences together, only splitting mid-sentence
    when a single sentence exceeds max_tokens.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        overlap_sentences: int = 1,
        encoding_name: str = "cl100k_base",
    ):
        """Initialize sentence chunker.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap_sentences: Number of sentences to overlap
            encoding_name: Tiktoken encoding name
        """
        self.max_tokens = max_tokens
        self.overlap_sentences = overlap_sentences
        self.encoding = tiktoken.get_encoding(encoding_name)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Simple sentence splitting - could be enhanced with NLTK/spaCy.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Basic sentence splitting on .!? followed by space or end
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str) -> Iterator[TextChunk]:
        """Split text into sentence-aware chunks.

        Args:
            text: Text to chunk

        Yields:
            TextChunk instances
        """
        if not text or not text.strip():
            return

        sentences = self._split_sentences(text)
        if not sentences:
            return

        chunk_index = 0
        current_sentences: list[str] = []
        current_tokens = 0
        char_position = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence exceeds limit, split it
            if sentence_tokens > self.max_tokens:
                # Flush current chunk if any
                if current_sentences:
                    chunk_text = " ".join(current_sentences)
                    yield TextChunk(
                        text=chunk_text,
                        index=chunk_index,
                        start_char=char_position - len(chunk_text),
                        end_char=char_position,
                        token_count=current_tokens,
                        content_hash=hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
                    )
                    chunk_index += 1
                    current_sentences = current_sentences[-self.overlap_sentences:]
                    current_tokens = sum(self.count_tokens(s) for s in current_sentences)

                # Use basic chunker for long sentence
                basic_chunker = TextChunker(self.max_tokens, 50)
                for sub_chunk in basic_chunker.chunk_text(sentence):
                    yield TextChunk(
                        text=sub_chunk.text,
                        index=chunk_index,
                        start_char=char_position + sub_chunk.start_char,
                        end_char=char_position + sub_chunk.end_char,
                        token_count=sub_chunk.token_count,
                        content_hash=sub_chunk.content_hash,
                    )
                    chunk_index += 1

                char_position += len(sentence) + 1
                continue

            # Check if adding this sentence exceeds limit
            if current_tokens + sentence_tokens > self.max_tokens and current_sentences:
                # Emit current chunk
                chunk_text = " ".join(current_sentences)
                yield TextChunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_char=char_position - len(chunk_text) - len(current_sentences) + 1,
                    end_char=char_position,
                    token_count=current_tokens,
                    content_hash=hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
                )
                chunk_index += 1

                # Keep overlap sentences
                current_sentences = current_sentences[-self.overlap_sentences:]
                current_tokens = sum(self.count_tokens(s) for s in current_sentences)

            # Add sentence to current chunk
            current_sentences.append(sentence)
            current_tokens += sentence_tokens
            char_position += len(sentence) + 1

        # Emit final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            yield TextChunk(
                text=chunk_text,
                index=chunk_index,
                start_char=char_position - len(chunk_text),
                end_char=char_position,
                token_count=current_tokens,
                content_hash=hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
            )


def create_chunker(
    strategy: str = "token",
    max_tokens: int = 512,
    overlap: int = 50,
) -> TextChunker | SentenceChunker:
    """Factory function to create appropriate chunker.

    Args:
        strategy: "token" or "sentence"
        max_tokens: Maximum tokens per chunk
        overlap: Overlap (tokens or sentences depending on strategy)

    Returns:
        Chunker instance
    """
    if strategy == "sentence":
        return SentenceChunker(
            max_tokens=max_tokens,
            overlap_sentences=overlap,
        )
    return TextChunker(
        max_tokens=max_tokens,
        overlap_tokens=overlap,
    )
