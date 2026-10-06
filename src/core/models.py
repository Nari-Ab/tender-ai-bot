from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendationEnum(str, Enum):
    PARTICIPATE = "УЧАСТВОВАТЬ"
    RISKY = "ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)"
    NEEDS_CLARIFICATION = "ТРЕБУЕТСЯ ЗАПРОС РАЗЪЯСНЕНИЙ"


class RiskFactor(BaseModel):
    category: str = Field(description="Категория риска, например: Штрафы, Сроки, Обеспечение, ТЗ")
    severity: str = Field(description="Уровень риска: LOW, MEDIUM, HIGH, CRITICAL")
    description: str = Field(description="Подробное описание риска для юриста и руководства")
    quote: Optional[str] = Field(default=None, description="Цитата из документации закупки")


class TenderInfo(BaseModel):
    id: str = Field(description="Реестровый номер закупки (ЕИС/Сбербанк-АСТ)")
    title: str = Field(description="Предмет закупки")
    customer: str = Field(description="Наименование организации заказчика")
    price: float = Field(description="Начальная максимальная цена контракта (НМЦК) в рублях")
    fz_law: str = Field(default="44-ФЗ", description="Федеральный закон: 44-ФЗ или 223-ФЗ")
    deadline_date: str = Field(description="Дата окончания подачи заявок")
    delivery_days: int = Field(default=30, description="Срок исполнения контракта в календарных днях")
    security_bid_amount: float = Field(default=0.0, description="Размер обеспечения заявки в рублях")
    security_contract_amount: float = Field(default=0.0, description="Размер обеспечения исполнения контракта в рублях")
    platform: str = Field(default="ЕИС Госзакупки", description="Электронная торговая площадка")


class TenderAnalysisResult(BaseModel):
    tender_id: str
    recommendation: RecommendationEnum
    risk_score: int = Field(ge=0, le=100, description="Оценка риска от 0 (безопасно) до 100 (токсично)")
    summary: str = Field(description="Краткая суть технического задания и объемов работ")
    financial_summary: str = Field(description="Финансовые условия, маржинальность, обеспечение")
    risks: List[RiskFactor] = Field(default_factory=list, description="Выявленные риски и ловушки заказчика")
    advantages: List[str] = Field(default_factory=list, description="Положительные факторы закупки")
    missing_docs: List[str] = Field(default_factory=list, description="Требуемые лицензии, СРО и сертификаты")
