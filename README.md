# TenderAI Sentinel

Autonomous procurement analysis and risk scoring for 44-FZ and 223-FZ tenders.

[![Tests](https://img.shields.io/badge/tests-15%20passed-1f9d55)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

TenderAI Sentinel monitors Russian procurement feeds (EIS Zakupki, Sberbank-AST), parses contract terms from PDF and DOCX technical specifications, and flags legal risks and penalty clauses via Sber GigaChat and YandexGPT APIs.

```bash
docker compose up --build    # run REST API and Telegram worker
pytest tests/ -v             # run integration test suite
```

### What an audit finding looks like

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
      └─ flag: exceeds statutory cap (PP RF No. 1042, 1/300 CBR rate) by ~20x

  ● contract_security — Notice Card, Section 4.2 (14,400,000.00 RUB / 30%)
      seen in: Procurement Requirements
      └─ flag: cash deposit required on customer account; bank guarantees prohibited

  ● licensing_requirement — Participant Qualification, Section 2.1
      seen in: Requirements, p. 3
      └─ flag: requires FSB Form 2 state secret license and Minpromtorg REP certificates

RECOMMENDATION
  Do not submit bid. High probability of contract default and placement into the RNP registry.
```

### Key Highlights

- **Feed Monitoring:** Pulls structured procurement notices from EIS Zakupki and trading platforms by OKPD2 and price filters.
- **Specification Parser:** Chunks contract documents (PDF, DOCX, TXT) and matches legal clauses against penalty formulas and delivery schedules.
- **LLM Scoring:** Sber GigaChat API and YandexGPT adapters with structured validation and a deterministic offline mock for testing.
- **Delivery:** Telegram bot (aiogram 3) for instant document review and FastAPI endpoints for external integrations.

### Local Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
uvicorn src.api.main:app --port 8000
python -m src.bot.bot
```

## License

[MIT](LICENSE)
