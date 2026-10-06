from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Bottom persistent keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Свежие закупки ИТ/ПО"), KeyboardButton(text="📊 Анализ примера (Рискованный)")],
            [KeyboardButton(text="📄 Проверить файл ТЗ"), KeyboardButton(text="⚙️ Статус LLM")],
        ],
        resize_keyboard=True,
    )


def get_tender_actions_keyboard(tender_id: str) -> InlineKeyboardMarkup:
    """Inline buttons attached to each tender notification card."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Запустить AI-разбор ТЗ",
                    callback_data=f"audit:{tender_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🌐 Открыть на ЕИС",
                    url=f"https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber={tender_id}"
                ),
            ]
        ]
    )
