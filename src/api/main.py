import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
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
STATIC_INDEX = os.path.join(os.path.dirname(__file__), "static", "index.html")


class AnalyzeRequest(BaseModel):
    tender_id: str
    tz_text: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    """Interactive production web dashboard on root URL."""
    if os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX)
    return HTMLResponse("<h1>TenderAI Sentinel</h1>")


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
