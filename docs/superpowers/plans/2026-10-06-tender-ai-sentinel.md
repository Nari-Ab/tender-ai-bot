# TenderAI Sentinel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready Russian procurement AI assistant and Telegram bot that monitors tenders (ЕИС/Сбербанк-АСТ), parses ТЗ documents (PDF/DOCX/TXT), evaluates risks with GigaChat/YandexGPT, and delivers Go/No-Go recommendations.

**Architecture:** Clean modular architecture in Python: Data models & Config -> Document Parser & Chunker -> Vector/RAG Retriever -> LLM Provider Layer (GigaChat + YandexGPT + Mock) -> Scoring Decision Engine -> Telegram Bot (aiogram 3) & FastAPI.

**Tech Stack:** Python 3.11+, Pydantic v2, aiogram 3, FastAPI, pypdf, python-docx, pytest, pytest-asyncio, Docker.

**Spec:** `docs/superpowers/specs/2026-10-06-tender-ai-sentinel-design.md`

## Global Constraints
- Python 3.11+ with strict type hinting and Pydantic v2 schemas.
- Must support zero-configuration offline demonstration (Mock LLM & sample procurement documents) alongside production API modes (GigaChat and YandexGPT).
- All tests must pass cleanly with `pytest`.
- Dockerfile and docker-compose.yml must be valid and ready for single-command launch.

## Review Focus
- Document parser handles malformed or empty documents without crashing.
- LLM JSON parsing falls back gracefully to heuristic scoring if an API returns unformatted text.
- Overly severe penalty clauses (e.g. > 1% per day or impossible 3-day delivery) trigger `ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)`.
- GigaChat and YandexGPT adapters handle network timeouts and missing API keys gracefully.
- Telegram bot handles document uploads of various formats (.pdf, .docx, .txt) and returns clean markdown responses.

---

### Task 1: Project Setup, Core Schemas & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/core/__init__.py`
- Create: `src/core/config.py`
- Create: `src/core/models.py`
- Create: `src/core/logger.py`
- Test: `tests/test_core_models.py`

**Interfaces:**
- Produces: `Settings`, `TenderInfo`, `RiskFactor`, `TenderAnalysisResult`, `RecommendationEnum`

- [ ] **Step 1: Write test for core data models and serialization**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `config.py`, `models.py`, and `logger.py`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit core configuration and models**

---

### Task 2: Document Processing & RAG Clause Retriever

**Files:**
- Create: `src/services/documents/__init__.py`
- Create: `src/services/documents/parser.py`
- Create: `src/services/documents/chunker.py`
- Create: `src/services/rag/__init__.py`
- Create: `src/services/rag/retriever.py`
- Create: `sample_data/tz_sample_ok.txt`
- Create: `sample_data/tz_sample_risky.txt`
- Test: `tests/test_documents.py`

**Interfaces:**
- Consumes: `src/core/models.py`
- Produces: `DocumentParser.extract_text(file_path_or_bytes, filename) -> str`, `DocumentChunker.chunk_tz(text) -> List[str]`, `ClauseRetriever.find_risk_clauses(text) -> Dict[str, List[str]]`

- [ ] **Step 1: Write failing test for document extraction and clause retrieval**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement DocumentParser, Chunker, and ClauseRetriever**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit document & RAG services**

---

### Task 3: Multi-Provider LLM Engine (GigaChat + YandexGPT + Mock)

**Files:**
- Create: `src/services/llm/__init__.py`
- Create: `src/services/llm/base.py`
- Create: `src/services/llm/gigachat.py`
- Create: `src/services/llm/yandexgpt.py`
- Create: `src/services/llm/mock_llm.py`
- Create: `src/services/llm/factory.py`
- Test: `tests/test_llm_providers.py`

**Interfaces:**
- Consumes: `TenderInfo`, `TenderAnalysisResult`, `Settings`
- Produces: `get_llm_provider(settings) -> LLMProvider`, `LLMProvider.analyze_tender(tender, tz_text) -> TenderAnalysisResult`

- [ ] **Step 1: Write failing test for LLM factory and providers**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement GigaChat, YandexGPT, and Mock LLM providers**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit LLM layer**

---

### Task 4: Scoring Engine & Procurement Feed Monitor

**Files:**
- Create: `src/services/scoring/__init__.py`
- Create: `src/services/scoring/engine.py`
- Create: `src/services/parsers/__init__.py`
- Create: `src/services/parsers/base.py`
- Create: `src/services/parsers/zakupki.py`
- Test: `tests/test_scoring.py`
- Test: `tests/test_zakupki_parser.py`

**Interfaces:**
- Consumes: `TenderInfo`, `ClauseRetriever`, `LLMProvider`
- Produces: `TenderScoringEngine.evaluate(tender, tz_text) -> TenderAnalysisResult`, `ZakupkiFeedMonitor.fetch_recent_tenders(keywords, min_price, max_price) -> List[TenderInfo]`

- [ ] **Step 1: Write failing test for scoring engine and tender feed**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement scoring engine with deterministic heuristic fallback + tender feed simulator/scraper**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit scoring and procurement feed services**

---

### Task 5: Telegram Bot (aiogram 3) & FastAPI Webhook/REST API

**Files:**
- Create: `src/bot/__init__.py`
- Create: `src/bot/keyboards.py`
- Create: `src/bot/handlers.py`
- Create: `src/bot/bot.py`
- Create: `src/api/__init__.py`
- Create: `src/api/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `TenderScoringEngine`, `ZakupkiFeedMonitor`, `Settings`
- Produces: FastAPI app with `/health`, `/api/analyze`, `/api/tenders`, and Telegram bot dispatcher.

- [ ] **Step 1: Write failing test for FastAPI API endpoints**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement aiogram 3 bot handlers and FastAPI endpoints**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit bot and API**

---

### Task 6: Dockerization, Portfolio Documentation & Recruiter Pitch

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md` (Professional documentation with architecture diagram, badges, and quickstart)
- Create: `PORTFOLIO_PITCH.md` (Ready-to-send response tailored for Natalia)

- [ ] **Step 1: Create Dockerfile and docker-compose.yml**
- [ ] **Step 2: Create comprehensive Russian/English README.md**
- [ ] **Step 3: Create tailored response text for the recruiter in PORTFOLIO_PITCH.md**
- [ ] **Step 4: Run entire test suite to ensure 100% green status**
- [ ] **Step 5: Final Git commit**
