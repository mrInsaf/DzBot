from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_kb():
    kb = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text="Назад", callback_data=f'back', )
    kb.add(cancel_button)
    return kb