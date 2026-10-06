import json
import uuid
import httpx
from typing import Optional
from src.core.models import TenderInfo, TenderAnalysisResult, RecommendationEnum, RiskFactor
from src.services.llm.base import LLMProvider
from src.services.rag.retriever import ClauseRetriever
from src.core.logger import get_logger

logger = get_logger("gigachat_provider")


class GigaChatProvider(LLMProvider):
    """
    Sber GigaChat API integration for Russian procurement documentation analysis.
    Uses official OAuth 2.0 exchange and structured JSON prompt responses.
    """

    OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    COMPLETIONS_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def __init__(self, credentials: Optional[str], scope: str = "GIGACHAT_API_PERS", verify_ssl: bool = False):
        self.credentials = credentials
        self.scope = scope
        self.verify_ssl = verify_ssl
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {self.credentials}",
        }
        data = {"scope": self.scope}

        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=15.0) as client:
            resp = await client.post(self.OAUTH_URL, headers=headers, data=data)
            resp.raise_for_status()
            payload = resp.json()
            self._access_token = payload["access_token"]
            return self._access_token

    async def analyze_tender(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        logger.info(f"[GigaChat] Analyzing tender '{tender.id}' via Sber GigaChat API")
        focused_context = ClauseRetriever.get_focused_context(tz_text, max_chars=4000)

        system_prompt = (
            "Ты — ведущий юрист и эксперт по закупкам 44-ФЗ и 223-ФЗ РФ. "
            "Твоя задача — объективно оценить техническое задание закупки на риски, скрытые условия и ловушки. "
            "Ответь СТРОГО в формате валидного JSON со следующей структурой:\n"
            "{\n"
            '  "recommendation": "УЧАСТВОВАТЬ" | "ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)" | "ТРЕБУЕТСЯ ЗАПРОС РАЗЪЯСНЕНИЙ",\n'
            '  "risk_score": <число от 0 до 100>,\n'
            '  "summary": "<краткая суть ТЗ>",\n'
            '  "financial_summary": "<финансовые условия и обеспечение>",\n'
            '  "risks": [{"category": "<Штрафы|Сроки|Обеспечение|ТЗ>", "severity": "<LOW|MEDIUM|HIGH|CRITICAL>", "description": "...", "quote": "..."}],\n'
            '  "advantages": ["<плюс 1>", "<плюс 2>"],\n'
            '  "missing_docs": ["<лицензия 1>"]\n'
            "}"
        )

        user_content = (
            f"Закупка: {tender.id} - {tender.title}\n"
            f"Заказчик: {tender.customer}\n"
            f"НМЦК: {tender.price:,.2f} руб. Срок поставки: {tender.delivery_days} дней.\n"
            f"Обеспечение заявки: {tender.security_bid_amount:,.2f} руб.\n"
            f"Обеспечение контракта: {tender.security_contract_amount:,.2f} руб.\n\n"
            f"ФРАГМЕНТЫ ТЕХНИЧЕСКОГО ЗАДАНИЯ:\n{focused_context}"
        )

        try:
            token = await self._get_access_token()
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            }
            body = {
                "model": "GigaChat:latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.2,
            }

            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
                res = await client.post(self.COMPLETIONS_URL, headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                raw_answer = data["choices"][0]["message"]["content"]

                # Parse JSON answer from model
                # Remove markdown fences if present
                clean_json = raw_answer.strip()
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
            logger.error(f"GigaChat API call failed: {e}. Falling back to heuristic mock analyzer.")
            from src.services.llm.mock_llm import MockLLMProvider
            mock = MockLLMProvider()
            result = await mock.analyze_tender(tender, tz_text)
            result.summary = f"[GigaChat Fallback: {e}] {result.summary}"
            return result
