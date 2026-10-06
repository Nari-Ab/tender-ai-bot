from abc import ABC, abstractmethod
from src.core.models import TenderInfo, TenderAnalysisResult


class LLMProvider(ABC):
    """Abstract interface for LLM tender analysis providers."""

    @abstractmethod
    async def analyze_tender(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        """
        Analyze tender conditions, terms of reference, penalties, and return structured Go/No-Go report.
        """
        pass
