import pytest
from src.services.parsers.zakupki import ZakupkiFeedMonitor


@pytest.mark.asyncio
async def test_zakupki_feed_monitor_filters():
    monitor = ZakupkiFeedMonitor()
    tenders = await monitor.fetch_recent_tenders(
        keywords=["сервер", "ПО", "оборудование"],
        min_price=1000000.0,
        max_price=50000000.0,
        limit=5
    )

    assert len(tenders) > 0
    for t in tenders:
        assert t.price >= 1000000.0
        assert t.price <= 50000000.0
        assert any(k.lower() in t.title.lower() for k in ["сервер", "по", "оборудование"])


@pytest.mark.asyncio
async def test_zakupki_feed_monitor_by_id():
    monitor = ZakupkiFeedMonitor()
    tender = await monitor.get_tender_by_id("0173200001424000123")
    assert tender is not None
    assert tender.id == "0173200001424000123"
    assert "ИТ" in tender.title or "ПО" in tender.title
