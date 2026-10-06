# TenderAI Sentinel

Сервис автоматизированного мониторинга государственных и коммерческих закупок (**44-ФЗ**, **223-ФЗ**) с разбором технической документации (PDF, DOCX) и скорингом юридических рисков через **GigaChat API** и **YandexGPT**.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.6+-2CA5E0.svg?logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Возможности

- **Мониторинг площадок:** Сбор и фильтрация закупок по ключевым словам, суммам (НМЦК), законам (44-ФЗ / 223-ФЗ) и площадкам (ЕИС Госзакупки, Сбербанк-АСТ).
- **RAG-пайплайн и разбор документации:** Извлечение текста из ТЗ и проектов контрактов (PDF, DOCX, TXT), семантический чанкинг с привязкой к статьям и разделам.
- **Анализ юридических рисков:**
  - Проверка условий неустойки и штрафов на превышение Постановления Правительства РФ № 1042 (1/300 ключевой ставки ЦБ);
  - Детекция нереалистичных сроков поставки (1–3 дня как признак ограничения конкуренции);
  - Анализ формы обеспечения (требование денежного залога вместо независимой банковской гарантии);
  - Проверка спецтребований (реестры Минпромторга, сертификаты СТ-1, лицензии ФСТЭК/ФСБ).
- **Интерфейсы доставки:**
  - **Telegram-бот на aiogram 3:** оперативные уведомления, интерактивные кнопки, приём файлов ТЗ напрямую в чат;
  - **FastAPI сервис:** REST API эндпоинты для вебхуков и интеграции с внутренними системами.
- **Гибридный LLM-провайдер:** поддержка GigaChat API (Сбер) и YandexGPT (Yandex Cloud) с возможностью переключения на локальный эвристический Mock-режим для тестирования.

---

## Архитектура

```text
[ Торговые площадки (ЕИС, Сбербанк-АСТ) ] ──► [ Feed Monitor ]
                                                     │
[ Файлы ТЗ (.pdf, .docx) ] ──► [ Document Parser ] ──┘
                                      │
                                      ▼
                             [ Semantic Chunker ]
                                      │
                                      ▼
                            [ Clause Retriever ]
                                      │
                                      ▼
                     [ LLM Engine (GigaChat / YandexGPT) ]
                                      │
                                      ▼
                         [ Scoring & Decision Engine ]
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
          [ Telegram Bot (aiogram 3) ]        [ FastAPI REST Service ]
```

---

## Пример работы скоринга

```text
⛔️ РЕЗЮМЕ АНАЛИЗА ЗАКУПКИ № 0373100012324000999 (44-ФЗ)
============================================================
📊 Рекомендация:    ВЫСОКИЙ РИСК (НЕ УЧАСТВОВАТЬ)
🔴 Индекс риска:    95 / 100
💰 Финансы:         НМЦК: 48,000,000 ₽ · Обеспечение: 14,400,000 ₽ (30%)

🚨 Выявленные риски:
• [Сроки | CRITICAL]: Срок поставки 3 календарных дня с даты заключения контракта
• [Штрафы | HIGH]: Неустойка 2% в день (960 000 ₽/день), превышает ПП РФ №1042
• [Обеспечение | HIGH]: Обеспечение 30% исключительно живыми деньгами на счет
• [Требования | MEDIUM]: Лицензия ФСБ формы 2 на работу с гостайной

Рекомендация: Высокий риск кассового разрыва и срыва сроков поставки.
```

---

## Быстрый запуск

### Через Docker Compose

```bash
git clone https://github.com/Nari-Ab/tender-ai-bot.git
cd tender-ai-bot

docker compose up --build
```

API доступно по адресу `http://localhost:8000`, документация Swagger UI — `http://localhost:8000/docs`.

### Локальная установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запуск тестов
pytest tests/ -v

# Запуск API
uvicorn src.api.main:app --reload --port 8000

# Запуск Telegram-бота
python -m src.bot.bot
```

---

## Конфигурация (.env)

```env
# Выбор провайдера: mock | gigachat | yandexgpt
LLM_PROVIDER=mock

# Сбер GigaChat API
GIGACHAT_CREDENTIALS=your_auth_key
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_VERIFY_SSL=false

# YandexGPT (Yandex Cloud)
YANDEX_API_KEY=your_api_key
YANDEX_FOLDER_ID=your_folder_id

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token

# Приложение
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## Тестирование

```bash
pytest tests/ -v
```

```text
tests/test_api.py::test_health_check_endpoint PASSED                     [  6%]
tests/test_api.py::test_get_tenders_endpoint PASSED                      [ 13%]
tests/test_api.py::test_analyze_tender_endpoint PASSED                   [ 20%]
tests/test_core_models.py::test_tender_info_creation PASSED              [ 26%]
tests/test_core_models.py::test_analysis_result_validation PASSED        [ 33%]
tests/test_core_models.py::test_settings_defaults PASSED                 [ 40%]
tests/test_documents.py::test_extract_text_from_txt PASSED               [ 46%]
tests/test_documents.py::test_chunker_splits_paragraphs PASSED           [ 53%]
tests/test_documents.py::test_clause_retriever_detects_risks PASSED      [ 60%]
tests/test_llm_providers.py::test_mock_llm_evaluates_risky_tender PASSED [ 66%]
tests/test_llm_providers.py::test_mock_llm_evaluates_ok_tender PASSED    [ 73%]
tests/test_llm_providers.py::test_factory_returns_mock_when_selected PASSED [ 80%]
tests/test_scoring.py::test_scoring_engine_full_workflow PASSED          [ 86%]
tests/test_zakupki_parser.py::test_zakupki_feed_monitor_filters PASSED   [ 93%]
tests/test_zakupki_parser.py::test_zakupki_feed_monitor_by_id PASSED     [100%]

============================== 15 passed in 0.20s ==============================
```

---

## Структура проекта

```text
tender-ai-bot/
├── sample_data/            # Примеры ТЗ для тестов (валидные и с рисками)
├── src/
│   ├── api/                # FastAPI маршруты (/health, /api/tenders, /api/analyze)
│   ├── bot/                # Telegram-бот на aiogram 3 (хэндлеры, кнопки)
│   ├── core/               # Pydantic настройки, модели данных, логгер
│   └── services/
│       ├── documents/      # Парсер документов (PDF/DOCX) и чанкер
│       ├── llm/            # Адаптеры GigaChat, YandexGPT, Mock LLM
│       ├── parsers/        # Монитор закупок ЕИС и Сбербанк-АСТ
│       ├── rag/            # Семантический поиск риск-кластеров
│       └── scoring/        # Движок скоринга и принятия решений
├── tests/                  # Pytest набор юнит- и интеграционных тестов
├── Dockerfile              # Сборка контейнера
├── docker-compose.yml      # Запуск API и Telegram-бота
└── requirements.txt        # Зависимости Python
```

---

## Лицензия

MIT License. См. файл [LICENSE](LICENSE).
