import io
import pytest
from src.services.documents.parser import DocumentParser
from src.services.documents.chunker import DocumentChunker
from src.services.rag.retriever import ClauseRetriever


def test_extract_text_from_txt():
    content = b"Sample procurement terms: Delivery in 10 days."
    text = DocumentParser.extract_text(content, filename="test.txt")
    assert "Sample procurement terms" in text


def test_chunker_splits_paragraphs():
    long_text = "\n\n".join([f"Раздел {i}. Описание требований номер {i}" for i in range(10)])
    chunks = DocumentChunker.chunk_tz(long_text, max_chunk_chars=100)
    assert len(chunks) > 1
    assert "Раздел 0" in chunks[0]


def test_clause_retriever_detects_risks():
    with open("sample_data/tz_sample_risky.txt", "r", encoding="utf-8") as f:
        risky_text = f.read()

    categories = ClauseRetriever.find_risk_clauses(risky_text)
    
    # Check that critical risk categories are found
    assert "penalties" in categories
    assert any("2%" in clause for clause in categories["penalties"])
    assert "deadlines" in categories
    assert any("3 календарных дней" in clause for clause in categories["deadlines"])
    assert "security" in categories
    assert any("30%" in clause for clause in categories["security"])
