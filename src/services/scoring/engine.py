from typing import Optional
from src.core.models import TenderInfo, TenderAnalysisResult, RecommendationEnum
from src.services.llm.base import LLMProvider
from src.services.llm.factory import get_llm_provider
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("tender_scoring_engine")


class TenderScoringEngine:
    """
    Central orchestration engine for evaluating procurement opportunities.
    Coordinates document retrieval, RAG, LLM scoring, and report formatting.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider(settings)

    async def evaluate(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        logger.info(f"Evaluating tender {tender.id} with provider {type(self.llm_provider).__name__}")
        return await self.llm_provider.analyze_tender(tender, tz_text)

    @staticmethod
    def format_telegram_summary(result: TenderAnalysisResult) -> str:
        """Formats analysis result into a clean, scannable Telegram Markdown message."""
        status_emoji = {
            RecommendationEnum.PARTICIPATE: "✅",
            RecommendationEnum.RISKY: "⛔️",
            RecommendationEnum.NEEDS_CLARIFICATION: "⚠️",
        }.get(result.recommendation, "ℹ️")

        risk_bar = "🟢" if result.risk_score < 40 else "🟡" if result.risk_score < 65 else "🔴"

        text = [
            f"*{status_emoji} РЕЗЮМЕ АНАЛИЗА ЗАКУПКИ № {result.tender_id}*",
            f"*{'=' * 30}*",
            f"📊 *Рекомендация:* {result.recommendation.value}",
            f"{risk_bar} *Индекс риска:* `{result.risk_score}/100`\n",
            f"📌 *Суть ТЗ:* {result.summary}",
            f"💰 *Финансы:* {result.financial_summary}\n",
        ]

        if result.risks:
            text.append("🚨 *Выявленные риски и ловушки:*")
            for r in result.risks:
                quote_part = f" _(Цитата: {r.quote[:80]}...)_" if r.quote else ""
                text.append(f"• *[{r.category} | {r.severity}]:* {r.description}{quote_part}")
            text.append("")

        if result.advantages:
            text.append("💎 *Плюсы и возможности:*")
            for adv in result.advantages:
                text.append(f"• {adv}")
            text.append("")

        if result.missing_docs:
            text.append("📋 *Обязательные лицензии / реестры:*")
            for doc in result.missing_docs:
                text.append(f"• {doc}")
            text.append("")

        text.append(f"_{'=' * 30}_")
        text.append("🤖 _Сгенерировано AI-ассистентом TenderAI Sentinel_")

        return "\n".join(text)
