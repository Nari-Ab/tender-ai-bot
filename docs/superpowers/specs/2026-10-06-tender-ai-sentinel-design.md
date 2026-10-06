# TenderAI Sentinel: Design Specification

## 1. Executive Summary
**TenderAI Sentinel** is an AI-powered automated procurement analysis and decision support platform. It solves the exact core problems listed in commercial procurement and tender monitoring:
- Multi-source monitoring of Russian procurement platforms (ЕИС Госзакупки 44-ФЗ / 223-ФЗ, Сбербанк-АСТ, B2B-Center).
- Semantic analysis of Terms of Reference (ТЗ) and contractual documentation (PDF, DOCX, TXT).
- Automated risk scoring and Go / No-Go decision recommendation (`УЧАСТВОВАТЬ` vs `НЕ УЧАСТВОВАТЬ (Высокий риск)`).
- Hybrid Russian-first LLM layer supporting **Sber GigaChat API**, **YandexGPT (Yandex Cloud) API**, and an offline Mock/Fallback provider for deterministic zero-cost demo evaluation.
- Asynchronous Telegram bot interface powered by `aiogram 3` and an enterprise REST API powered by `FastAPI`.

---

## 2. Technical Stack
- **Language**: Python 3.11+
- **LLM Adapters**:
  - `gigachat` SDK / REST API (Sber)
  - Yandex Cloud Foundation Models (YandexGPT v3 / Lite API)
  - Offline Deterministic Heuristic LLM Mock (for local testing without keys)
- **Document Processing**: `pypdf`, `python-docx`, regex chunker with tender domain heuristics (штрафы, пени, обеспечение, сроки).
- **RAG & Search**: In-memory semantic vector retriever + BM25 keyword matching for high-precision retrieval of legal & penalty clauses.
- **Bot Framework**: `aiogram 3.x` (asynchronous, FSM, inline keyboards, file upload handler).
- **API Framework**: `FastAPI` + `Pydantic v2` (for webhook & external CRM/ERP integration).
- **Testing & Quality**: `pytest`, `pytest-asyncio`, PEP8 strict typing.
- **Deployment**: `Docker`, `docker-compose.yml`, multi-stage builds.

---

## 3. Architecture & Module Structure

```text
tender-ai-bot/
├── docs/
│   └── superpowers/
│       ├── specs/2026-10-06-tender-ai-sentinel-design.md
│       └── plans/2026-10-06-tender-ai-sentinel.md
├── src/
│   ├── core/
│   │   ├── config.py           # Pydantic BaseSettings, API keys, env vars
│   │   ├── logger.py           # Structured logging
│   │   └── models.py           # Tender, RiskFactor, AnalysisResult schemas
│   ├── services/
│   │   ├── llm/
│   │   │   ├── base.py         # Abstract LLMProvider interface
│   │   │   ├── gigachat.py     # Sber GigaChat API client
│   │   │   ├── yandexgpt.py    # YandexGPT Cloud API client
│   │   │   ├── mock_llm.py     # Offline intelligent mock for testing
│   │   │   └── factory.py      # Provider selector & fallback mechanism
│   │   ├── documents/
│   │   │   ├── parser.py       # PDF/DOCX/TXT text extraction
│   │   │   └── chunker.py      # Semantic chunking tuned for procurement docs
│   │   ├── rag/
│   │   │   └── retriever.py    # Clause search (penalties, deadlines, criteria)
│   │   ├── scoring/
│   │   │   └── engine.py       # Go/No-Go rule-based + LLM decision logic
│   │   └── parsers/
│   │       ├── base.py         # Base procurement scraper interface
│   │       └── zakupki.py      # EIS & Sberbank-AST tender feed monitor
│   ├── bot/
│   │   ├── bot.py              # Aiogram 3 dispatcher initialization
│   │   ├── handlers.py         # /start, /tenders, file upload handler
│   │   └── keyboards.py        # Inline interactive buttons
│   └── api/
│       └── main.py             # FastAPI REST endpoints for webhook/healthcheck
├── tests/
│   ├── test_documents.py       # Tests for document text extraction & chunking
│   ├── test_llm_providers.py   # Tests for GigaChat, YandexGPT, and Mock adapters
│   ├── test_scoring.py         # Tests for Go/No-Go decision engine
│   └── test_zakupki_parser.py  # Tests for tender feed monitoring
├── sample_data/
│   ├── tz_sample_ok.txt        # Realistic low-risk sample procurement spec
│   └── tz_sample_risky.txt     # Realistic high-risk sample procurement spec
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Key Schemas & Interfaces

### 4.1 Data Models (`src/core/models.py`)
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RecommendationEnum(str, Enum):
    PARTICIPATE = "УЧАСТВОВАТЬ"
    RISKY = "ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)"
    NEEDS_CLARIFICATION = "ТРЕБУЕТСЯ ЗАПРОС РАЗЪЯСНЕНИЙ"

class RiskFactor(BaseModel):
    category: str  # "Штрафы", "Сроки", "Обеспечение", "Технические ограничения"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str
    quote: Optional[str] = None

class TenderInfo(BaseModel):
    id: str
    title: str
    customer: str
    price: float
    fz_law: str  # "44-ФЗ" / "223-ФЗ"
    deadline_date: str
    delivery_days: int
    security_bid_amount: float
    security_contract_amount: float
    platform: str

class TenderAnalysisResult(BaseModel):
    tender_id: str
    recommendation: RecommendationEnum
    risk_score: int  # 0 to 100 (0 = safe, 100 = toxic/impossible)
    summary: str
    financial_summary: str
    risks: List[RiskFactor]
    advantages: List[str]
    missing_docs: List[str]
```

### 4.2 LLM Interface (`src/services/llm/base.py`)
```python
from abc import ABC, abstractmethod
from src.core.models import TenderAnalysisResult, TenderInfo

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_tender(self, tender: TenderInfo, tz_text: str) -> TenderAnalysisResult:
        pass
```

---

## 5. Security & Verification Strategy
1. Safe secrets management via `.env` (no hardcoded tokens).
2. SSL cert handling for GigaChat (using Sberbank root certificates or verification toggle).
3. 100% executable test coverage with pytest across parser, chunker, scoring, and LLM factory.
