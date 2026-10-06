import pytest
from src.core.models import TenderInfo, RecommendationEnum
from src.services.scoring.engine import TenderScoringEngine
from src.services.llm.mock_llm import MockLLMProvider


@pytest.mark.asyncio
async def test_scoring_engine_full_workflow():
    with open("sample_data/tz_sample_risky.txt", "r", encoding="utf-8") as f:
        tz_content = f.read()

    tender = TenderInfo(
        id="0373100012324000999",
        title="Срочная поставка вычислительных комплексов для ЦОД",
        customer="Федеральное агентство специального назначения",
        price=48000000.0,
        fz_law="44-ФЗ",
        deadline_date="2026-11-20",
        delivery_days=3,
        security_bid_amount=2400000.0,
        security_contract_amount=14400000.0,
        platform="ЕИС Госзакупки",
    )

    engine = TenderScoringEngine(llm_provider=MockLLMProvider())
    result = await engine.evaluate(tender=tender, tz_text=tz_content)

    assert result.tender_id == tender.id
    assert result.recommendation == RecommendationEnum.RISKY
    assert result.risk_score >= 70
    assert len(result.risks) > 0
    # Verify report formatting
    markdown_report = engine.format_telegram_summary(result)
    assert "ВЫСОКИЙ РИСК" in markdown_report
    assert "0373100012324000999" in markdown_report
