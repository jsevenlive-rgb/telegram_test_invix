from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import get_settings


def main_menu(is_owner: bool = False) -> ReplyKeyboardMarkup:
    settings = get_settings()
    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(
                text="🛒 Открыть каталог",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        ],
        [KeyboardButton(text="🏪 Создать магазин")],
    ]
    if is_owner:
        rows.append([KeyboardButton(text="➕ Создать товар")])
        rows.append([KeyboardButton(text="📦 Мои магазины")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def shops_inline(shops: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🏪 {s['name']}",
                callback_data=f"pick_shop:{s['id']}",
            )
        ]
        for s in shops
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
