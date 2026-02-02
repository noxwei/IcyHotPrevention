"""Unit tests for text chunking."""

import pytest

from iety.processing.chunking import TextChunker, SentenceChunker, create_chunker


class TestTextChunker:
    """Tests for TextChunker."""

    @pytest.fixture
    def chunker(self):
        """Create a text chunker."""
        return TextChunker(max_tokens=100, overlap_tokens=10)

    def test_count_tokens(self, chunker):
        """Token counting should work correctly."""
        text = "Hello world"
        count = chunker.count_tokens(text)
        assert count > 0
        assert count == 2  # "Hello" and "world"

    def test_short_text_single_chunk(self, chunker):
        """Short text should result in a single chunk."""
        text = "This is a short sentence."
        chunks = list(chunker.chunk_text(text))

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0

    def test_empty_text_no_chunks(self, chunker):
        """Empty text should result in no chunks."""
        chunks = list(chunker.chunk_text(""))
        assert len(chunks) == 0

        chunks = list(chunker.chunk_text("   "))
        assert len(chunks) == 0

    def test_long_text_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        chunker = TextChunker(max_tokens=10, overlap_tokens=2)
        text = "This is a longer text that should be split into multiple chunks for testing purposes."
        chunks = list(chunker.chunk_text(text))

        assert len(chunks) > 1
        # Check indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunks_have_content_hash(self, chunker):
        """Each chunk should have a content hash."""
        text = "Some text to chunk."
        chunks = list(chunker.chunk_text(text))

        assert all(chunk.content_hash for chunk in chunks)
        assert len(chunks[0].content_hash) == 16  # First 16 chars of SHA-256

    def test_chunk_with_metadata(self, chunker):
        """chunk_with_metadata should include source info."""
        text = "Text to chunk with metadata."
        chunks = list(chunker.chunk_with_metadata(
            text,
            source_id="test-123",
            source_schema="usaspending",
            source_table="awards",
        ))

        assert len(chunks) > 0
        chunk = chunks[0]
        assert chunk["source_id"] == "test-123"
        assert chunk["source_schema"] == "usaspending"
        assert chunk["source_table"] == "awards"


class TestSentenceChunker:
    """Tests for SentenceChunker."""

    @pytest.fixture
    def chunker(self):
        """Create a sentence chunker."""
        return SentenceChunker(max_tokens=50, overlap_sentences=1)

    def test_sentence_boundaries_respected(self, chunker):
        """Chunks should respect sentence boundaries when possible."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = list(chunker.chunk_text(text))

        # Check that sentences aren't split mid-word
        for chunk in chunks:
            # Should start with capital or be a continuation
            assert chunk.text[0].isupper() or chunk.text.startswith(" ")

    def test_long_sentence_split(self):
        """Very long sentences should be split."""
        chunker = SentenceChunker(max_tokens=10, overlap_sentences=0)
        long_sentence = "This is a very long sentence " * 20
        chunks = list(chunker.chunk_text(long_sentence))

        assert len(chunks) > 1


class TestCreateChunker:
    """Tests for create_chunker factory."""

    def test_create_token_chunker(self):
        """Factory should create TextChunker for 'token' strategy."""
        chunker = create_chunker(strategy="token", max_tokens=512, overlap=50)
        assert isinstance(chunker, TextChunker)
        assert chunker.max_tokens == 512
        assert chunker.overlap_tokens == 50

    def test_create_sentence_chunker(self):
        """Factory should create SentenceChunker for 'sentence' strategy."""
        chunker = create_chunker(strategy="sentence", max_tokens=512, overlap=2)
        assert isinstance(chunker, SentenceChunker)
        assert chunker.max_tokens == 512
        assert chunker.overlap_sentences == 2

    def test_default_is_token_chunker(self):
        """Default strategy should be token chunking."""
        chunker = create_chunker()
        assert isinstance(chunker, TextChunker)
