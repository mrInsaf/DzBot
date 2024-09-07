import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_kb():
    kb = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text="Назад", callback_data=f'back', )
    kb.add(cancel_button)
    return kb


def create_assignment_text(subject: str, deadline: datetime.datetime, description: str):
    return f"\n<b>{subject}</b>\n\n<u>Дедлайн</u> {deadline}\n{description}\n\n -----------------\n"
