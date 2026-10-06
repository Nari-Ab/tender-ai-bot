import re
from typing import List
from src.core.models import TenderInfo, TenderAnalysisResult, RecommendationEnum, RiskFactor
from src.services.llm.base import LLMProvider
from src.services.rag.retriever import ClauseRetriever
from src.core.logger import get_logger

logger = get_logger("mock_llm")


class MockLLMProvider(LLMProvider):
    """
    Intelligent heuristic mock LLM engine.
    Allows zero-token offline testing and demonstration of the complete system,
    analyzing real tender clauses with domain-specific procurement rules.
    """

    async def analyze_tender(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        logger.info(f"[MockLLM] Analyzing tender '{tender.id}' ({tender.title})")
        clauses = ClauseRetriever.find_risk_clauses(tz_text)
        risks: List[RiskFactor] = []
        advantages: List[str] = []
        missing_docs: List[str] = []
        risk_score = 15  # baseline baseline score

        # 1. Delivery timeline analysis
        if tender.delivery_days <= 5 or re.search(r"\b[1-5]\s+(?:календарн\w*|рабоч\w*)\s+дн", tz_text.lower()):
            risk_score += 35
            risks.append(RiskFactor(
                category="Сроки",
                severity="CRITICAL",
                description=f"Критически короткий срок исполнения: {tender.delivery_days} дней. Признак 'заточки' под конкретного поставщика.",
                quote=clauses["deadlines"][0] if clauses["deadlines"] else f"Срок: {tender.delivery_days} дней"
            ))
        else:
            advantages.append(f"Реалистичный срок поставки/работ: {tender.delivery_days} дней")

        # 2. Penalty & sanctions analysis
        high_penalty = False
        for c in clauses["penalties"]:
            c_lower = c.lower()
            # If standard government decree 1042 / 1/300 is mentioned, it is NOT risky
            if "1042" in c_lower or "1/300" in c_lower:
                continue

            # Look for exorbitant penalties (>= 1% per day or 2% etc)
            if re.search(r"\b[1-9]\s*%", c_lower) or "без права апелляции" in c_lower:
                high_penalty = True
                risks.append(RiskFactor(
                    category="Штрафы",
                    severity="HIGH",
                    description="Кабальный размер неустойки/пени, превышающий стандартные нормы Постановления Правительства №1042.",
                    quote=c[:200]
                ))
                risk_score += 30
                break

        if not high_penalty:
            advantages.append("Стандартные штрафные санкции в рамках ПП РФ №1042 (1/300 ключевой ставки ЦБ)")

        # 3. Security deposit requirements
        sec_ratio = (tender.security_contract_amount / tender.price) if tender.price > 0 else 0
        if sec_ratio >= 0.20 or "исключительно в виде залога" in tz_text.lower():
            risk_score += 25
            risks.append(RiskFactor(
                category="Обеспечение",
                severity="HIGH",
                description=f"Высокое обеспечение исполнения контракта ({int(sec_ratio*100)}% от цены) или запрет банковских гарантий.",
                quote=clauses["security"][0] if clauses["security"] else f"Обеспечение: {tender.security_contract_amount:,.2f} руб."
            ))
        elif sec_ratio > 0:
            advantages.append(f"Адекватный размер обеспечения контракта: {int(sec_ratio*100)}%")

        # 4. Strict participant requirements (licenses, registry)
        for req_chunk in clauses["requirements"]:
            if "гостайн" in req_chunk.lower() or "фсб" in req_chunk.lower():
                missing_docs.append("Лицензия ФСБ на работу с гостайной")
                risk_score += 20
                risks.append(RiskFactor(
                    category="Требования к участникам",
                    severity="MEDIUM",
                    description="Требуется лицензия ФСБ на работу со сведениями, составляющими государственную тайну.",
                    quote=req_chunk[:180]
                ))
            if "реестр минпромторг" in req_chunk.lower() or "ст-1" in req_chunk.lower():
                missing_docs.append("Сертификат СТ-1 / включение в реестр РЭП Минпромторга")

        # 5. Advance payment
        if re.search(r"авансирование[:\s]+(?:не\s+предусмотрено|0%)", tz_text, re.IGNORECASE):
            risks.append(RiskFactor(
                category="Финансирование",
                severity="LOW",
                description="Авансирование отсутствует, требуется 100% кассовый разрыв до момента приемки.",
                quote=None
            ))
        elif re.search(r"аванс\w*\s+([1-9]\d*)%", tz_text, re.IGNORECASE):
            match = re.search(r"аванс\w*\s+([1-9]\d*)%", tz_text, re.IGNORECASE)
            advantages.append(f"Предусмотрен аванс в размере {match.group(1)}%")

        risk_score = min(100, max(0, risk_score))

        # Decision threshold
        if risk_score >= 60:
            rec = RecommendationEnum.RISKY
        elif risk_score >= 40:
            rec = RecommendationEnum.NEEDS_CLARIFICATION
        else:
            rec = RecommendationEnum.PARTICIPATE

        summary = (
            f"Закупка '{tender.title}' для заказчика '{tender.customer}' по закону {tender.fz_law}. "
            f"НМЦК составляет {tender.price:,.2f} руб."
        )

        fin_summary = (
            f"Обеспечение заявки: {tender.security_bid_amount:,.2f} руб. "
            f"Обеспечение контракта: {tender.security_contract_amount:,.2f} руб. "
            f"Срок: {tender.delivery_days} дн."
        )

        return TenderAnalysisResult(
            tender_id=tender.id,
            recommendation=rec,
            risk_score=risk_score,
            summary=summary,
            financial_summary=fin_summary,
            risks=risks,
            advantages=advantages,
            missing_docs=missing_docs,
        )
