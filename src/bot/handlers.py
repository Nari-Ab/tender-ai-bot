import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from src.bot.keyboards import get_main_reply_keyboard, get_tender_actions_keyboard
from src.services.parsers.zakupki import ZakupkiFeedMonitor
from src.services.scoring.engine import TenderScoringEngine
from src.services.documents.parser import DocumentParser
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger("bot_handlers")
router = Router(name="tender_bot_router")

feed_monitor = ZakupkiFeedMonitor()
scoring_engine = TenderScoringEngine()


@router.message(CommandStart())
async def cmd_start(message: Message):
    greeting = (
        "👋 *Приветствую! Я TenderAI Sentinel — интеллектуальный ассистент по закупкам.*\n\n"
        "🎯 *Что я умею:*\n"
        "• Ежедневный мониторинг закупок (ЕИС Госзакупки 44-ФЗ/223-ФЗ, Сбербанк-АСТ)\n"
        "• Автоматический разбор ТЗ и проектов контрактов через *GigaChat / YandexGPT*\n"
        "• Поиск кабальных условий, штрафов и скрытых требований к поставщикам\n"
        "• Выдача четкой рекомендации: *«УЧАСТВОВАТЬ»* или *«НЕ УЧАСТВОВАТЬ (Высокий риск)»*\n\n"
        "📎 *Отправьте мне файл ТЗ (.pdf, .docx, .txt) или выберите действие ниже:*"
    )
    await message.answer(greeting, parse_mode="Markdown", reply_markup=get_main_reply_keyboard())


@router.message(F.text == "🔍 Свежие закупки ИТ/ПО")
async def show_recent_tenders(message: Message):
    await message.answer("⏳ *Сканирую реестр ЕИС и Сбербанк-АСТ...*", parse_mode="Markdown")
    tenders = await feed_monitor.fetch_recent_tenders(limit=3)

    for t in tenders:
        card = (
            f"📋 *Закупка № {t.id}* ({t.fz_law})\n"
            f"🏢 *Заказчик:* {t.customer}\n"
            f"📦 *Предмет:* {t.title}\n"
            f"💵 *НМЦК:* `{t.price:,.2f} ₽`\n"
            f"⏱ *Срок исполнения:* `{t.delivery_days} дн.`\n"
            f"🏛 *Площадка:* {t.platform}\n"
            f"📅 *Окончание подачи:* {t.deadline_date}"
        )
        await message.answer(
            card,
            parse_mode="Markdown",
            reply_markup=get_tender_actions_keyboard(t.id),
        )


@router.message(F.text == "📊 Анализ примера (Рискованный)")
async def analyze_risky_sample(message: Message):
    await message.answer("🧠 *Запускаю глубокий аудит ТЗ через LLM (поиск штрафов и скрытых условий)...*", parse_mode="Markdown")
    sample_file = "sample_data/tz_sample_risky.txt"
    with open(sample_file, "r", encoding="utf-8") as f:
        tz_content = f.read()

    tender = await feed_monitor.get_tender_by_id("0373100012324000999")
    if not tender:
        await message.answer("Закупка не найдена.")
        return

    result = await scoring_engine.evaluate(tender=tender, tz_text=tz_content)
    report = scoring_engine.format_telegram_summary(result)
    await message.answer(report, parse_mode="Markdown")


@router.message(F.text == "⚙️ Статус LLM")
async def show_llm_status(message: Message):
    status_text = (
        "⚙️ *Статус конфигурации AI:*\n\n"
        f"• *Активный LLM-провайдер:* `{settings.LLM_PROVIDER}`\n"
        f"• *Сбер GigaChat API:* `{'Настроен' if settings.GIGACHAT_CREDENTIALS else 'Режим демо / fallback'}`\n"
        f"• *YandexGPT Cloud:* `{'Настроен' if settings.YANDEX_API_KEY else 'Режим демо / fallback'}`\n"
        f"• *Сервер API:* `{settings.APP_HOST}:{settings.APP_PORT}`\n"
    )
    await message.answer(status_text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("audit:"))
async def on_audit_callback(query: CallbackQuery):
    tender_id = query.data.split(":")[1]
    await query.answer("Запускаю анализ ТЗ...")
    await query.message.answer(f"🔍 *Анализирую тендер № {tender_id}...*", parse_mode="Markdown")

    tender = await feed_monitor.get_tender_by_id(tender_id)
    if not tender:
        await query.message.answer("Закупка не найдена в реестре.")
        return

    # Check if we have sample text or title
    sample_path = "sample_data/tz_sample_risky.txt" if tender.delivery_days < 10 else "sample_data/tz_sample_ok.txt"
    tz_text = tender.title
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            tz_text = f.read()

    result = await scoring_engine.evaluate(tender=tender, tz_text=tz_text)
    report = scoring_engine.format_telegram_summary(result)
    await query.message.answer(report, parse_mode="Markdown")


@router.message(F.document)
async def handle_document_upload(message: Message):
    doc = message.document
    filename = doc.file_name or "document.txt"
    await message.answer(f"📥 *Получен файл:* `{filename}`. *Извлекаю текст и формирую RAG-выборку...*", parse_mode="Markdown")

    try:
        # Download file in bot environment
        file = await message.bot.get_file(doc.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        content_bytes = file_bytes.read()

        extracted_text = DocumentParser.extract_text(content_bytes, filename=filename)

        if not extracted_text or len(extracted_text.strip()) < 20:
            await message.answer("⚠️ Не удалось извлечь текст из документа или файл пустой.")
            return

        await message.answer(f"📑 *Текст успешно извлечен ({len(extracted_text)} символов). Запускаю LLM-скоринг...*", parse_mode="Markdown")

        dummy_tender = await feed_monitor.get_tender_by_id("0173200001424000123")
        result = await scoring_engine.evaluate(tender=dummy_tender, tz_text=extracted_text)
        report = scoring_engine.format_telegram_summary(result)
        await message.answer(report, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при обработке документа: {str(e)}")
