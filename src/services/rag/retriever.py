import re
from typing import Dict, List
from src.services.documents.chunker import DocumentChunker


class ClauseRetriever:
    """
    Semantic and keyword-targeted RAG clause retriever for procurement documentation.
    Extracts high-risk sections (penalties, deadlines, securities, strict participant demands).
    """

    PATTERNS: Dict[str, List[str]] = {
        "penalties": [
            r"штраф", r"пен[ияе]", r"неустойк", r"санкци", r"ответственност", r"1042"
        ],
        "deadlines": [
            r"срок", r"календарн\w*\s+дн", r"рабоч\w*\s+дн", r"поставк", r"график", r"период"
        ],
        "security": [
            r"обеспечени", r"гарантийн", r"банковск\w*\s+гаранти", r"залог", r"депозит"
        ],
        "requirements": [
            r"лицензи", r"сро", r"реестр", r"ст-1", r"минпромторг", r"фстэк", r"фсб", r"сертификат", r"гост"
        ],
        "payment": [
            r"аванс", r"оплат", r"расчет", r"рассрочк", r"банковск\w*\s+дн"
        ]
    }

    @classmethod
    def find_risk_clauses(cls, text: str) -> Dict[str, List[str]]:
        """
        Parses text into chunks and returns matching risk clauses grouped by category.
        """
        chunks = DocumentChunker.chunk_tz(text, max_chunk_chars=800)
        results: Dict[str, List[str]] = {category: [] for category in cls.PATTERNS}

        for chunk in chunks:
            chunk_lower = chunk.lower()
            for category, regex_list in cls.PATTERNS.items():
                for pattern in regex_list:
                    if re.search(pattern, chunk_lower):
                        if chunk not in results[category]:
                            results[category].append(chunk)
                        break

        return results

    @classmethod
    def get_focused_context(cls, text: str, max_chars: int = 4000) -> str:
        """
        Builds a compact, high-signal prompt context for the LLM containing the most
        critical clauses instead of blowing up context window with boilerplate text.
        """
        clauses_by_cat = cls.find_risk_clauses(text)
        sections = []

        for cat, items in clauses_by_cat.items():
            if items:
                joined = "\n---\n".join(items[:2])
                sections.append(f"### Секция: {cat.upper()}\n{joined}")

        combined = "\n\n".join(sections)
        if len(combined) > max_chars:
            return combined[:max_chars] + "\n...[контекст сокращен]"
        return combined if combined.strip() else text[:max_chars]
