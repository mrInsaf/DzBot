import datetime
import inspect

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.leaders import leaders
from days_of_week import days_of_week
from db import select_subject_by_subject_id, select_group_id_by_chat_id, select_subjects_by_group_id, select_leaders
from models.Assignment import Assignment
from models.Deadline import Deadline


def create_kb():
    kb = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text="Назад", callback_data=f'back', )
    kb.add(cancel_button)
    return kb


def create_assignment_text(subject: str, deadline_str: str, description: str, week_day, days_remaining):
    return f"\n<b>{subject}</b>\n\n<u>Дедлайн</u> {deadline_str} {week_day} ({days_remaining} дней осталось)\nОписание: {description}\n\n -----------------\n"


def create_assignment_text_from_assignment_obj(assignment: Assignment):
    return (f"\n<b>{assignment.subject}</b>\n\n"
            f"<u>Дедлайн</u> {assignment.deadline.string} {assignment.deadline.day_of_week} "
            f"({assignment.deadline.days_remaining} дней осталось)\n"
            f"Описание: {assignment.description}\n\n -----------------\n")

def days_until(target_date: datetime.datetime) -> int:
    """Функция считает количество дней до указанной даты"""
    today = datetime.datetime.now().date()  # Получаем текущую дату без времени
    target_date = target_date.date()  # Убираем время из целевой даты
    delta = target_date - today  # Вычисляем разницу между датами
    return delta.days


async def add_assignment_accept_dz_logic(description: str, state: FSMContext):
    kb = create_kb()
    kb.add(InlineKeyboardButton(text="Все верно", callback_data="accept"))
    kb.adjust(2)

    data = await state.get_data()
    result_str = "Проверьте правильность заполнения дз: \n"

    subject_id = data['subject_id']
    subject = select_subject_by_subject_id(subject_id)
    deadline = data['deadline']
    print(f"data is: {data}")

    assignment_text = create_assignment_text(
        subject,
        deadline.string,
        description,
        deadline.day_of_week,
        deadline.days_remaining
    )
    result_str += assignment_text
    return kb, result_str


async def choose_subject(callback: CallbackQuery, state: FSMContext):
    if callback.data != "back":
        group_id = select_group_id_by_chat_id(callback.from_user.id)
        await state.update_data(group_id=group_id)
    else:
        data = await state.get_data()
        group_id = data['group_id']
    subjects_by_group = select_subjects_by_group_id(group_id)
    kb = create_kb()
    for subject in subjects_by_group:
        kb.add(
            InlineKeyboardButton(text=subject[1], callback_data=f"{subject[0]}")
        )
    kb.adjust(1)
    await callback.message.answer(text="Выберите предмет", reply_markup=kb.as_markup())


def dttm_to_string(dttm: datetime) -> str:
    return dttm.strftime("%d.%m.%Y")


def string_to_dttm(dttm_str: str):
    date_format = "%d.%m"

    # Парсинг строки в объект datetime без указания года
    parsed_date = datetime.datetime.strptime(dttm_str, date_format)

    # Добавление текущего года
    current_year = datetime.datetime.now().year
    parsed_date = parsed_date.replace(year=current_year)
    return parsed_date


def find_by_id(objects, object_id):
    return next((obj for obj in objects if obj.id == object_id), None)


def find_assignment_from_data(callback:CallbackQuery, data: dict) -> Assignment:
    assignments = data['assignments']
    assignment_id = int(callback.data)
    selected_assignment: Assignment = find_by_id(assignments, assignment_id)
    return selected_assignment


def create_assignments_list(raw_assignments: list):
    assignment_list = []
    for assignment in raw_assignments:
        assignment_obj = Assignment(
            id=assignment[0],
            subject=assignment[1],
            group_id=assignment[2],
            description=assignment[3],
            deadline=assignment[4],
            created_at=assignment[5],
        )
        if assignment_obj.deadline.dttm >= datetime.datetime.now():
            assignment_list.append(assignment_obj)
    return assignment_list


def caller_func():
    # Получаем текущий фрейм
    current_frame = inspect.currentframe()
    # Переходим на один уровень вверх по стеку (к вызывающей функции)
    outer_frames = inspect.getouterframes(current_frame)
    return outer_frames[3].function


def is_leader(username):
    # leaders = select_leaders()
    return username in leaders
