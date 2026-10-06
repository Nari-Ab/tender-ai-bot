from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.models import TenderInfo


class ProcurementScraper(ABC):
    """Abstract interface for procurement platforms and aggregators."""

    @abstractmethod
    async def fetch_recent_tenders(
        self,
        keywords: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10
    ) -> List[TenderInfo]:
        pass

    @abstractmethod
    async def get_tender_by_id(self, tender_id: str) -> Optional[TenderInfo]:
        pass
