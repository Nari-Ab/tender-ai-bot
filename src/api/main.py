from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.core.config import settings
from src.core.models import TenderInfo, TenderAnalysisResult
from src.services.parsers.zakupki import ZakupkiFeedMonitor
from src.services.scoring.engine import TenderScoringEngine
from src.core.logger import get_logger

logger = get_logger("api_main")

app = FastAPI(
    title="TenderAI Sentinel API",
    description="REST API for automated Russian procurement monitoring and LLM analysis (ЕИС, Сбербанк-АСТ, GigaChat, YandexGPT)",
    version="1.0.0",
)

feed_monitor = ZakupkiFeedMonitor()
scoring_engine = TenderScoringEngine()


class AnalyzeRequest(BaseModel):
    tender_id: str
    tz_text: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    """Interactive developer dashboard on root URL."""
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TenderAI Sentinel</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            background-color: #0b0f19;
            color: #e2e8f0;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid #1e293b;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{
            font-size: 24px;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }}
        .tagline {{
            color: #94a3b8;
            font-size: 14px;
            margin: 0;
        }}
        .status-bar {{
            display: flex;
            gap: 16px;
            margin-top: 12px;
            font-size: 13px;
        }}
        .badge {{
            background: #1e293b;
            padding: 4px 10px;
            border-radius: 4px;
            color: #38bdf8;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 16px;
            margin-top: 0;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 8px;
            color: #f1f5f9;
        }}
        button {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 13px;
            cursor: pointer;
            margin-right: 8px;
            margin-bottom: 8px;
        }}
        button:hover {{
            background: #1d4ed8;
        }}
        button.secondary {{
            background: #1f2937;
            color: #cbd5e1;
        }}
        button.secondary:hover {{
            background: #374151;
        }}
        pre {{
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 6px;
            padding: 14px;
            font-size: 13px;
            line-height: 1.5;
            color: #e5e7eb;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        a {{
            color: #38bdf8;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>TenderAI Sentinel</h1>
            <p class="tagline">Automated procurement analysis and risk scoring (44-FZ / 223-FZ)</p>
            <div class="status-bar">
                <span class="badge">Engine: {settings.LLM_PROVIDER}</span>
                <span class="badge">Status: Online</span>
                <span><a href="/docs" target="_blank">OpenAPI Docs (/docs) &rarr;</a></span>
            </div>
        </header>

        <div class="card">
            <h2>Тестирование скоринга ТЗ</h2>
            <p style="font-size: 13px; color: #94a3b8;">Выберите закупку для запуска семантического аудита:</p>
            <button onclick="runAudit('0373100012324000999', 'Закупка оборудования ЦОД: 48 млн руб, срок 3 дня, неустойка 2% в день, залог 30%')">
                Анализ: Серверы ЦОД (48 млн ₽, критический риск)
            </button>
            <button class="secondary" onclick="runAudit('0173200001424000123', 'Сопровождение ПО: 3.5 млн руб, срок 180 дней, штрафы по ПП 1042')">
                Анализ: Сопровождение ПО (3.5 млн ₽, безопасная)
            </button>
            <pre id="auditOutput">Нажмите кнопку выше для запуска анализа...</pre>
        </div>

        <div class="card">
            <h2>Реестр закупок (ЕИС Госзакупки / Сбербанк-АСТ)</h2>
            <button class="secondary" onclick="loadTenders()">Загрузить список закупок (/api/tenders)</button>
            <pre id="tendersOutput">Нажмите кнопку для загрузки записей...</pre>
        </div>
    </div>

    <script>
        async function runAudit(tenderId, tzText) {{
            const out = document.getElementById('auditOutput');
            out.textContent = 'Выполняется аудит через ' + '{settings.LLM_PROVIDER}' + '...';
            try {{
                const res = await fetch('/api/analyze', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ tender_id: tenderId, tz_text: tzText }})
                }});
                const data = await res.json();
                out.textContent = JSON.stringify(data, null, 2);
            }} catch (err) {{
                out.textContent = 'Ошибка: ' + err.message;
            }}
        }}

        async function loadTenders() {{
            const out = document.getElementById('tendersOutput');
            out.textContent = 'Запрос к /api/tenders...';
            try {{
                const res = await fetch('/api/tenders');
                const data = await res.json();
                out.textContent = JSON.stringify(data, null, 2);
            }} catch (err) {{
                out.textContent = 'Ошибка: ' + err.message;
            }}
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/health")
async def health_check():
    """Service health check and active LLM provider inspection."""
    return {
        "status": "ok",
        "service": "TenderAI Sentinel",
        "version": "1.0.0",
        "provider": settings.LLM_PROVIDER,
    }


@app.get("/api/tenders", response_model=List[TenderInfo])
async def search_tenders(
    keywords: Optional[str] = Query(None, description="Comma-separated keywords, e.g. 'сервер, ПО'"),
    min_price: Optional[float] = Query(None, description="Minimum contract price in RUB"),
    max_price: Optional[float] = Query(None, description="Maximum contract price in RUB"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search and filter procurement records from monitoring feeds."""
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else None
    tenders = await feed_monitor.fetch_recent_tenders(
        keywords=kw_list,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )
    return tenders


@app.post("/api/analyze", response_model=TenderAnalysisResult)
async def analyze_tender(request: AnalyzeRequest):
    """Run full RAG and LLM audit on a tender to determine Go/No-Go recommendation."""
    tender = await feed_monitor.get_tender_by_id(request.tender_id)
    if not tender:
        tender = TenderInfo(
            id=request.tender_id,
            title="Пользовательская закупка",
            customer="Не указан",
            price=0.0,
            deadline_date="По ТЗ",
            delivery_days=30,
        )

    tz_text = request.tz_text or tender.title
    result = await scoring_engine.evaluate(tender=tender, tz_text=tz_text)
    return result
