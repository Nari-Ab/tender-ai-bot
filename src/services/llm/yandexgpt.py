import json
import httpx
from typing import Optional
from src.core.models import TenderInfo, TenderAnalysisResult, RecommendationEnum, RiskFactor
from src.services.llm.base import LLMProvider
from src.services.rag.retriever import ClauseRetriever
from src.core.logger import get_logger

logger = get_logger("yandexgpt_provider")


class YandexGPTProvider(LLMProvider):
    """
    YandexGPT (Yandex Cloud Foundation Models) API client for procurement document analysis.
    """

    COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def __init__(self, api_key: Optional[str], folder_id: Optional[str], model_uri: Optional[str] = None):
        self.api_key = api_key
        self.folder_id = folder_id
        self.model_uri = model_uri or f"gpt://{folder_id}/yandexgpt/latest" if folder_id else None

    async def analyze_tender(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        logger.info(f"[YandexGPT] Analyzing tender '{tender.id}' via Yandex Cloud")
        focused_context = ClauseRetriever.get_focused_context(tz_text, max_chars=4000)

        system_prompt = (
            "Ты — ведущий юрисконсульт и эксперт по тендерам и госзакупкам. "
            "Проведи глубокий аудит ТЗ и проекта контракта на кабальные условия, риски и штрафы. "
            "Ответь СТРОГО в виде JSON объекта:\n"
            "{\n"
            '  "recommendation": "УЧАСТВОВАТЬ" | "ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)" | "ТРЕБУЕТСЯ ЗАПРОС РАЗЪЯСНЕНИЙ",\n'
            '  "risk_score": <целое число 0-100>,\n'
            '  "summary": "<краткое резюме>",\n'
            '  "financial_summary": "<финансовый анализ>",\n'
            '  "risks": [{"category": "<Штрафы|Сроки|Обеспечение|ТЗ>", "severity": "<LOW|MEDIUM|HIGH|CRITICAL>", "description": "...", "quote": "..."}],\n'
            '  "advantages": ["<плюс 1>"],\n'
            '  "missing_docs": ["<требование 1>"]\n'
            "}"
        )

        user_content = (
            f"Закупка: {tender.id} {tender.title}\n"
            f"Заказчик: {tender.customer}\n"
            f"Цена: {tender.price:,.2f} руб. Срок: {tender.delivery_days} дн.\n\n"
            f"ТЕКСТ ДОКУМЕНТАЦИИ:\n{focused_context}"
        )

        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "x-folder-id": self.folder_id,
            }
            body = {
                "modelUri": self.model_uri,
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.2,
                    "maxTokens": "2000"
                },
                "messages": [
                    {"role": "system", "text": system_prompt},
                    {"role": "user", "text": user_content}
                ]
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(self.COMPLETION_URL, headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                raw_text = data["result"]["alternatives"][0]["message"]["text"]

                clean_json = raw_text.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]

                parsed = json.loads(clean_json.strip())
                return TenderAnalysisResult(
                    tender_id=tender.id,
                    recommendation=parsed.get("recommendation", RecommendationEnum.NEEDS_CLARIFICATION),
                    risk_score=parsed.get("risk_score", 50),
                    summary=parsed.get("summary", tender.title),
                    financial_summary=parsed.get("financial_summary", f"{tender.price:,.2f} руб."),
                    risks=[RiskFactor(**r) for r in parsed.get("risks", [])],
                    advantages=parsed.get("advantages", []),
                    missing_docs=parsed.get("missing_docs", []),
                )

        except Exception as e:
            logger.error(f"YandexGPT API call failed: {e}. Falling back to heuristic mock analyzer.")
            from src.services.llm.mock_llm import MockLLMProvider
            mock = MockLLMProvider()
            result = await mock.analyze_tender(tender, tz_text)
            result.summary = f"[YandexGPT Fallback: {e}] {result.summary}"
            return result
