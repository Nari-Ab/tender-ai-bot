# TenderAI Sentinel

### Automated procurement document analysis and risk scoring for 44-FZ and 223-FZ tenders

[![CI](https://img.shields.io/badge/tests-15%20passed-1f9d55)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

TenderAI Sentinel monitors Russian state and commercial procurement feeds (EIS Zakupki, Sberbank-AST), parses contract terms from PDF and DOCX technical specifications, and flags legal risks and penalty clauses via GigaChat and YandexGPT APIs.

```bash
docker compose up --build          # run REST API and Telegram audit worker
pytest tests/ -v                   # verify all 15 integration tests
```

What an audit finding looks like (synthetic procurement run, trimmed):

```text
tender-ai audit — clause evaluation on notice 0373100012324000999 (44-FZ)

✗ VERDICT: HIGH_RISK (score: 95/100)
  Customer: Federal Special Agency · Price: 48,000,000.00 RUB

CRITICAL CLAUSES IDENTIFIED (4)

  ● delivery_timeline — Section 1.3 (3 calendar days)
      seen in: Technical Specification, p. 2
      └─ flag: impossible turnaround for hardware assembly; indicator of restricted competition

  ● penalty_rate — Contract Draft, Section 8.1 (2.0% per day)
      seen in: Contract Terms, p. 14
      └─ flag: exceeds Russian statutory cap (PP RF No. 1042, 1/300 CBR rate) by ~20x

  ● contract_security — Notice Card, Section 4.2 (14,400,000.00 RUB / 30%)
      seen in: Procurement Requirements
      └─ flag: cash deposit required on customer account; bank guarantees prohibited

  ● licensing_requirement — Participant Qualification, Section 2.1
      seen in: Requirements, p. 3
      └─ flag: requires FSB Form 2 state secret license and Minpromtorg REP certificates

RECOMMENDATION
  Do not submit bid. High probability of contract default and placement into the Unscrupulous Suppliers Registry (RNP).
```

- **Monitors feeds.** Pulls structured procurement notices from EIS Zakupki and electronic trading platforms by OKPD2, price bounds, and customer keywords.
- **Extracts terms.** Chunks contract specifications (PDF, DOCX, TXT) and matches legal clauses against penalty formulas, security demands, and delivery schedules.
- **Evaluates with LLMs.** Adapters for Sberbank GigaChat API and YandexGPT with structured JSON validation and a deterministic local fallback for testing without external credentials.
- **Reports via Bot and API.** Delivers audit summaries through an aiogram 3 Telegram worker and exposes FastAPI endpoints for ERP/CRM integration.

## Usage

### Docker

```bash
git clone https://github.com/Nari-Ab/tender-ai-bot.git
cd tender-ai-bot
docker compose up --build
```

The REST service listens on `http://localhost:8000`. OpenAPI documentation is available at `/docs`.

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start FastAPI service
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Start Telegram worker
python -m src.bot.bot
```

## Configuration

Environment variables are defined in `.env` (copy from `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | Active engine: `mock`, `gigachat`, `yandexgpt` | `mock` |
| `GIGACHAT_CREDENTIALS` | Sber GigaChat API authorization key | - |
| `GIGACHAT_SCOPE` | GigaChat auth scope (`GIGACHAT_API_PERS` or `GIGACHAT_API_CORP`) | `GIGACHAT_API_PERS` |
| `GIGACHAT_VERIFY_SSL` | Enable/disable TLS certificate verification | `false` |
| `YANDEX_API_KEY` | Yandex Cloud API key | - |
| `YANDEX_FOLDER_ID` | Yandex Cloud folder identifier | - |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | - |
| `APP_PORT` | HTTP port for the FastAPI service | `8000` |

## Project Layout

```text
tender-ai-bot/
├── src/
│   ├── api/            # FastAPI routes (/health, /api/tenders, /api/analyze)
│   ├── bot/            # aiogram 3 Telegram worker
│   ├── core/           # Configuration, Pydantic schemas, logging
│   └── services/
│       ├── documents/  # PDF/DOCX parsers and semantic chunker
│       ├── llm/        # GigaChat, YandexGPT, and mock adapters
│       ├── parsers/    # Procurement feed aggregators
│       ├── rag/        # Clause extraction and risk pattern matching
│       └── scoring/    # Evaluation and Go/No-Go decision engine
├── tests/              # Pytest test suite
├── sample_data/        # Sample specifications for evaluation
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## License

[MIT](LICENSE)
