import pytest
from src.core.models import (
    RecommendationEnum,
    RiskFactor,
    TenderInfo,
    TenderAnalysisResult,
)
from src.core.config import Settings


def test_tender_info_creation():
    tender = TenderInfo(
        id="0173200001424000123",
        title="Поставка серверного оборудования и СХД",
        customer="ГКУ 'Информационный Город'",
        price=12500000.0,
        fz_law="44-ФЗ",
        deadline_date="2026-11-01",
        delivery_days=30,
        security_bid_amount=125000.0,
        security_contract_amount=1250000.0,
        platform="ЕИС Госзакупки",
    )
    assert tender.id == "0173200001424000123"
    assert tender.price == 12500000.0
    assert tender.fz_law == "44-ФЗ"


def test_analysis_result_validation():
    risk = RiskFactor(
        category="Штрафы",
        severity="HIGH",
        description="Неустойка 1.5% в день превышает ключевую ставку ЦБ РФ",
        quote="Пункт 8.4: За каждый день просрочки начисляется штраф 1.5%",
    )
    result = TenderAnalysisResult(
        tender_id="0173200001424000123",
        recommendation=RecommendationEnum.RISKY,
        risk_score=78,
        summary="Закупка серверного оборудования с кабальными условиями неустойки.",
        financial_summary="НМЦК: 12.5 млн руб. Обеспечение контракта: 10%.",
        risks=[risk],
        advantages=["Крупный заказчик", "Авансирование 20%"],
        missing_docs=["Лицензия ФСТЭК на СЗИ"],
    )
    assert result.recommendation == RecommendationEnum.RISKY
    assert result.risk_score == 78
    assert len(result.risks) == 1
    assert result.risks[0].severity == "HIGH"


def test_settings_defaults():
    settings = Settings(LLM_PROVIDER="mock")
    assert settings.LLM_PROVIDER == "mock"
    assert settings.APP_PORT == 8000
