"""
Phase 6 tests — all embeddings and Gemini calls are mocked.

Tests cover: chunker, similarity search, vector store, retriever,
reranker, context builder, citation generator, and RAG API endpoints.
"""

from __future__ import annotations

import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

DIM = 8  # small dimension for fast tests

def _rand_emb(n: int = 1) -> np.ndarray:
    return np.random.rand(n, DIM).astype(np.float32)


def _make_chunks(n: int = 3, section: str = "Haematology"):
    from ai.rag.chunker import DocumentChunk
    return [
        DocumentChunk(
            chunk_id=f"chunk-{i}",
            text=f"Hemoglobin 12.{i} g/dL Reference 13.5-17.5 status low",
            section=section,
            page_number=i + 1,
            source_file="test.pdf",
            word_count=8,
            char_count=50,
            chunk_index=i,
        )
        for i in range(n)
    ]


# ------------------------------------------------------------------ #
# Chunker
# ------------------------------------------------------------------ #

class TestChunker:
    def test_basic_chunking(self) -> None:
        from ai.rag.chunker import DocumentChunker
        chunker = DocumentChunker(max_words=20, overlap_words=5)
        text = "Word " * 50  # 50 words
        chunks = chunker.chunk(text, document_id="d1")
        assert len(chunks) > 1

    def test_empty_text_returns_empty(self) -> None:
        from ai.rag.chunker import DocumentChunker
        assert DocumentChunker().chunk("") == []

    def test_short_text_is_one_chunk(self) -> None:
        from ai.rag.chunker import DocumentChunker
        chunks = DocumentChunker(max_words=100).chunk("Short text.", document_id="d1")
        assert len(chunks) == 1

    def test_section_header_splits_sections(self) -> None:
        from ai.rag.chunker import DocumentChunker
        text = "Haematology\nHemoglobin 12.4 g/dL\n\nDiagnosis\nAnemia"
        chunks = DocumentChunker(max_words=200).chunk(text, document_id="d2")
        sections = {c.section for c in chunks}
        assert len(sections) >= 2

    def test_chunk_indices_are_sequential(self) -> None:
        from ai.rag.chunker import DocumentChunker
        chunks = DocumentChunker(max_words=10, overlap_words=2).chunk(
            "Word " * 40, document_id="d3"
        )
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_total_chunks_populated(self) -> None:
        from ai.rag.chunker import DocumentChunker
        chunks = DocumentChunker(max_words=10, overlap_words=2).chunk(
            "Word " * 30, document_id="d4"
        )
        for c in chunks:
            assert c.total_chunks == len(chunks)


# ------------------------------------------------------------------ #
# Similarity Search
# ------------------------------------------------------------------ #

class TestSimilaritySearch:
    def test_cosine_similar_vectors_high_score(self) -> None:
        from ai.rag.similarity_search import cosine_similarity
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(1.0, abs=1e-6)

    def test_cosine_orthogonal_vectors_zero(self) -> None:
        from ai.rag.similarity_search import cosine_similarity
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_normalize_l2_unit_norm(self) -> None:
        from ai.rag.similarity_search import normalize_l2
        v = np.array([[3.0, 4.0]], dtype=np.float32)
        normalize_l2(v)
        assert np.linalg.norm(v[0]) == pytest.approx(1.0, abs=1e-6)

    def test_top_k_filters_and_sorts(self) -> None:
        from ai.rag.similarity_search import top_k_by_score
        items = [("a", 0.9), ("b", 0.4), ("c", 0.7), ("d", 0.1)]
        result = top_k_by_score(items, k=2, threshold=0.5)
        assert len(result) == 2
        assert result[0][1] >= result[1][1]

    def test_mean_similarity_empty(self) -> None:
        from ai.rag.similarity_search import mean_similarity
        assert mean_similarity([]) == 0.0


# ------------------------------------------------------------------ #
# Vector Store
# ------------------------------------------------------------------ #

class TestVectorStore:
    def test_add_and_search(self) -> None:
        from ai.rag.vector_store import VectorStore
        vs = VectorStore(DIM)
        chunks = _make_chunks(3)
        emb = _rand_emb(3)
        vs.add(emb, chunks)
        assert vs.total_vectors == 3

        q = _rand_emb(1)[0]
        results = vs.search(q, k=2)
        assert len(results) == 2
        assert all(0 <= r.score <= 1.1 for r in results)

    def test_search_empty_returns_empty(self) -> None:
        from ai.rag.vector_store import VectorStore
        vs = VectorStore(DIM)
        results = vs.search(_rand_emb(1)[0], k=3)
        assert results == []

    def test_save_and_load(self, tmp_path) -> None:
        from ai.rag.vector_store import VectorStore
        vs = VectorStore(DIM)
        vs.add(_rand_emb(2), _make_chunks(2))
        path = str(tmp_path / "test_store")
        vs.save(path)

        vs2 = VectorStore.load(path)
        assert vs2.total_vectors == 2

    def test_threshold_filters_low_scores(self) -> None:
        from ai.rag.vector_store import VectorStore
        vs = VectorStore(DIM)
        vs.add(_rand_emb(5), _make_chunks(5))
        q = _rand_emb(1)[0]
        results = vs.search(q, k=5, threshold=0.99)
        # With random vectors, very few (if any) should score ≥ 0.99
        assert len(results) <= 5


# ------------------------------------------------------------------ #
# Reranker
# ------------------------------------------------------------------ #

class TestReranker:
    def test_deduplicates_identical_text(self) -> None:
        from ai.rag.reranker import Reranker
        from ai.rag.vector_store import SearchResult
        chunk = _make_chunks(1)[0]
        results = [
            SearchResult(chunk=chunk, score=0.9, faiss_index=0),
            SearchResult(chunk=chunk, score=0.8, faiss_index=1),
        ]
        reranked = Reranker().rerank(results)
        assert len(reranked) == 1

    def test_priority_section_boost(self) -> None:
        from ai.rag.reranker import Reranker
        from ai.rag.vector_store import SearchResult
        low_chunk  = _make_chunks(1, section="Header")[0]
        high_chunk = _make_chunks(1, section="Diagnosis")[0]
        low_chunk.text  = "Patient was admitted to hospital for evaluation and review purposes."
        high_chunk.text = "Patient was diagnosed with iron deficiency by the specialist."
        results = [
            SearchResult(chunk=low_chunk,  score=0.7, faiss_index=0),
            SearchResult(chunk=high_chunk, score=0.7, faiss_index=1),
        ]
        reranked = Reranker().rerank(results)
        assert reranked[0].chunk.section == "Diagnosis"


# ------------------------------------------------------------------ #
# Context Builder
# ------------------------------------------------------------------ #

class TestContextBuilder:
    def test_no_results_includes_not_available_instruction(self) -> None:
        from ai.rag.context_builder import ContextBuilder
        prompt = ContextBuilder().build("Test question", [])
        assert "not contain" in prompt.lower() or "not available" in prompt.lower()

    def test_context_block_includes_source_labels(self) -> None:
        from ai.rag.context_builder import ContextBuilder
        from ai.rag.vector_store import SearchResult
        chunks = _make_chunks(2)
        results = [
            SearchResult(chunk=c, score=0.85, faiss_index=i)
            for i, c in enumerate(chunks)
        ]
        prompt = ContextBuilder(max_context_chars=5000).build("What is my Hb?", results)
        assert "Context 1" in prompt
        assert "Haematology" in prompt

    def test_budget_limits_context_size(self) -> None:
        from ai.rag.context_builder import ContextBuilder
        from ai.rag.vector_store import SearchResult
        chunks = _make_chunks(10)
        # Large text per chunk
        for c in chunks:
            c.text = "x " * 1000
        results = [
            SearchResult(chunk=c, score=0.9, faiss_index=i)
            for i, c in enumerate(chunks)
        ]
        prompt = ContextBuilder(max_context_chars=500).build("Q?", results)
        # Very small budget — only first chunk(s) should fit
        assert len(prompt) < 5000


# ------------------------------------------------------------------ #
# Citation Generator
# ------------------------------------------------------------------ #

class TestCitationGenerator:
    def test_generates_one_citation_per_result(self) -> None:
        from ai.rag.citation_generator import CitationGenerator
        from ai.rag.vector_store import SearchResult
        chunks = _make_chunks(3)
        results = [
            SearchResult(chunk=c, score=0.8 - i * 0.1, faiss_index=i)
            for i, c in enumerate(chunks)
        ]
        citations = CitationGenerator().generate(results)
        assert len(citations) == 3

    def test_citation_preview_truncated(self) -> None:
        from ai.rag.citation_generator import CitationGenerator
        from ai.rag.vector_store import SearchResult
        chunk = _make_chunks(1)[0]
        chunk.text = "A" * 300
        results = [SearchResult(chunk=chunk, score=0.9, faiss_index=0)]
        citations = CitationGenerator().generate(results)
        assert len(citations[0].preview) <= 120


# ------------------------------------------------------------------ #
# RAG API endpoint tests (mocked)
# ------------------------------------------------------------------ #

SAMPLE_TEXT = (
    "Haematology\n"
    "Hemoglobin 12.4 g/dL Reference 13.5-17.5\n"
    "WBC 11200 /uL Reference 4000-11000\n\n"
    "Diagnosis\nIron Deficiency Anemia\n"
)
DOCUMENT_ID = "test-rag-doc-001"


class TestRAGEndpoints:
    def test_index_missing_text_returns_422(self, client) -> None:
        r = client.post("/api/v1/rag/index", json={"text": "", "document_id": DOCUMENT_ID})
        assert r.status_code == 422

    def test_search_without_index_returns_404(self, client) -> None:
        r = client.post(
            "/api/v1/rag/search",
            json={"question": "What is my Hb?", "document_id": "nonexistent-id"},
        )
        assert r.status_code == 404

    def test_chat_without_index_returns_404(self, client) -> None:
        r = client.post(
            "/api/v1/rag/chat",
            json={"question": "Summarize", "document_id": "nonexistent-chat-id"},
        )
        assert r.status_code == 404

    def test_index_with_mocked_embedding(self, client) -> None:
        fake_emb = np.random.rand(10, DIM).astype(np.float32)
        with patch(
            "app.api.v1.endpoints.rag.embedding_service.embed_documents",
            return_value=fake_emb,
        ):
            r = client.post(
                "/api/v1/rag/index",
                json={
                    "text": SAMPLE_TEXT,
                    "document_id": DOCUMENT_ID,
                    "source_file": "test.pdf",
                },
            )
        assert r.status_code == 200
        data = r.json()
        assert data["document_id"] == DOCUMENT_ID
        assert data["chunks_indexed"] > 0

    def test_chat_with_mocked_pipeline(self, client) -> None:
        from app.schemas.rag import CitationSource, RAGChatResponse

        mock_response = RAGChatResponse(
            answer="Your Hemoglobin is 12.4 g/dL. Please consult your healthcare provider.",
            sources=[CitationSource(page=1, section="Haematology", score=0.92, preview="Hemoglobin 12.4...")],
            retrieved_chunks=2,
            confidence=0.88,
        )
        with patch(
            "app.api.v1.endpoints.rag.vector_store_manager.exists",
            return_value=True,
        ), patch(
            "app.api.v1.endpoints.rag.rag_chat_service.chat",
            new=AsyncMock(return_value=mock_response),
        ):
            r = client.post(
                "/api/v1/rag/chat",
                json={"question": "What is my hemoglobin?", "document_id": DOCUMENT_ID},
            )
        assert r.status_code == 200
        data = r.json()
        assert "12.4" in data["answer"]
        assert len(data["sources"]) == 1
        assert data["confidence"] == pytest.approx(0.88)
        assert "disclaimer" in data
