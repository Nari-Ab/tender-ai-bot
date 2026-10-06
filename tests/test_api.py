import pytest
from httpx import ASGITransport, AsyncClient
from src.api.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "provider" in data


@pytest.mark.asyncio
async def test_get_tenders_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/tenders?keywords=сервер")
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) > 0
        assert "сервер" in items[0]["title"].lower()


@pytest.mark.asyncio
async def test_analyze_tender_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "tender_id": "0173200001424000123",
            "tz_text": "Стандартное техническое задание. Срок 60 дней. Штрафы 1042."
        }
        response = await client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        analysis = response.json()
        assert "recommendation" in analysis
        assert "risk_score" in analysis
