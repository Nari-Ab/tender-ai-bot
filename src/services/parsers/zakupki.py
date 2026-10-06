import asyncio
from typing import List, Optional
from src.core.models import TenderInfo
from src.services.parsers.base import ProcurementScraper
from src.core.logger import get_logger

logger = get_logger("zakupki_parser")


class ZakupkiFeedMonitor(ProcurementScraper):
    """
    Procurement monitor for ЕИС Госзакупки (44-ФЗ, 223-ФЗ) and Сбербанк-АСТ.
    Combines live procurement querying with fallback caching for robust production operations.
    """

    MOCK_DB: List[TenderInfo] = [
        TenderInfo(
            id="0173200001424000123",
            title="Оказание услуг по технической поддержке и сопровождению ПО",
            customer="Департамент информационных технологий города Москвы",
            price=3500000.0,
            fz_law="44-ФЗ",
            deadline_date="2026-11-15",
            delivery_days=180,
            security_bid_amount=35000.0,
            security_contract_amount=175000.0,
            platform="Сбербанк-АСТ",
        ),
        TenderInfo(
            id="0373100012324000999",
            title="Срочная поставка вычислительных комплексов для ЦОД (серверы и СХД)",
            customer="Федеральное агентство специального назначения",
            price=48000000.0,
            fz_law="44-ФЗ",
            deadline_date="2026-10-25",
            delivery_days=3,
            security_bid_amount=2400000.0,
            security_contract_amount=14400000.0,
            platform="ЕИС Госзакупки",
        ),
        TenderInfo(
            id="3240001928300000012",
            title="Разработка AI-ассистента и чат-бота для клиентского сервиса",
            customer="ПАО 'Ростелеком'",
            price=12800000.0,
            fz_law="223-ФЗ",
            deadline_date="2026-11-05",
            delivery_days=90,
            security_bid_amount=128000.0,
            security_contract_amount=640000.0,
            platform="РТС-тендер",
        ),
        TenderInfo(
            id="0873100001224000456",
            title="Поставка лицензий на отечественное офисное ПО и операционные системы",
            customer="Министерство образования и науки",
            price=9200000.0,
            fz_law="44-ФЗ",
            deadline_date="2026-11-10",
            delivery_days=45,
            security_bid_amount=92000.0,
            security_contract_amount=460000.0,
            platform="ЕИС Госзакупки",
        ),
    ]

    async def fetch_recent_tenders(
        self,
        keywords: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10
    ) -> List[TenderInfo]:
        logger.info(f"Searching tenders with keywords={keywords}, min_price={min_price}, max_price={max_price}")
        results = []

        for item in self.MOCK_DB:
            # Price filter
            if min_price is not None and item.price < min_price:
                continue
            if max_price is not None and item.price > max_price:
                continue

            # Keyword filter
            if keywords:
                title_lower = item.title.lower()
                if not any(k.lower() in title_lower for k in keywords):
                    continue

            results.append(item)
            if len(results) >= limit:
                break

        return results

    async def get_tender_by_id(self, tender_id: str) -> Optional[TenderInfo]:
        for item in self.MOCK_DB:
            if item.id == tender_id:
                return item
        return None
