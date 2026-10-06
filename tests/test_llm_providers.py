import pytest
from src.core.models import TenderInfo, RecommendationEnum
from src.core.config import Settings
from src.services.llm.factory import get_llm_provider
from src.services.llm.mock_llm import MockLLMProvider


@pytest.fixture
def sample_tender():
    return TenderInfo(
        id="0373100012324000999",
        title="Поставка серверов и СХД",
        customer="Минцифры",
        price=48000000.0,
        fz_law="44-ФЗ",
        deadline_date="2026-11-20",
        delivery_days=3,
        security_bid_amount=2400000.0,
        security_contract_amount=14400000.0,
        platform="ЕИС Госзакупки",
    )


@pytest.mark.asyncio
async def test_mock_llm_evaluates_risky_tender(sample_tender):
    with open("sample_data/tz_sample_risky.txt", "r", encoding="utf-8") as f:
        tz_text = f.read()

    provider = MockLLMProvider()
    result = await provider.analyze_tender(sample_tender, tz_text)

    assert result.tender_id == sample_tender.id
    assert result.recommendation == RecommendationEnum.RISKY
    assert result.risk_score >= 70
    assert len(result.risks) >= 2
    assert any("штраф" in r.description.lower() or "неустойк" in r.description.lower() for r in result.risks)


@pytest.mark.asyncio
async def test_mock_llm_evaluates_ok_tender():
    with open("sample_data/tz_sample_ok.txt", "r", encoding="utf-8") as f:
        tz_text = f.read()

    tender_ok = TenderInfo(
        id="0173200001424000123",
        title="Сопровождение ПО",
        customer="ДИТ",
        price=3500000.0,
        fz_law="44-ФЗ",
        deadline_date="2026-12-01",
        delivery_days=180,
        security_bid_amount=35000.0,
        security_contract_amount=175000.0,
        platform="Сбербанк-АСТ",
    )

    provider = MockLLMProvider()
    result = await provider.analyze_tender(tender_ok, tz_text)

    assert result.recommendation == RecommendationEnum.PARTICIPATE
    assert result.risk_score < 40
    assert len(result.advantages) > 0


def test_factory_returns_mock_when_selected():
    settings = Settings(LLM_PROVIDER="mock")
    provider = get_llm_provider(settings)
    assert isinstance(provider, MockLLMProvider)
