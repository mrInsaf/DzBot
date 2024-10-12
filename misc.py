import datetime
import inspect
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.leaders import leaders
from days_of_week import days_of_week
from db import *
from models.Assignment import Assignment
from models.Deadline import Deadline
from states import AddAssignment


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


async def send_add_assignment_notification_to_group(bot: Bot, group_id: int, assignment_text: str):
    text = f"Добавлено новое ДЗ. Описание:\n{assignment_text}\nДля перехода в начало нажмите /start"
    await send_notification_to_group(bot, group_id, text)


async def send_edit_assignment_new_description_notification_to_group(bot: Bot, group_id: int, assignment_text: str):
    text = f"Изменилось описание в одном из ДЗ. Описание:\n{assignment_text}\nДля перехода в начало нажмите /start"
    await send_notification_to_group(bot, group_id, text)


async def send_edit_assignment_new_deadline_notification_to_group(bot: Bot, group_id: int, assignment_text: str):
    text = f"Изменился дедлайн в одном из ДЗ. Описание:\n{assignment_text}\nДля перехода в начало нажмите /start"
    await send_notification_to_group(bot, group_id, text)


async def send_notification_to_group(bot: Bot, group_id: int, text: str):
    students = select_students_chat_ids_by_group_id(group_id)
    for student in students:

        await bot.send_message(chat_id=int(student[0]), text=text)

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
            subject_id=assignment[6],
        )

        if assignment_obj.deadline.dttm.date() >= datetime.datetime.today().date():
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


async def share_assignment_start_logic(assignment_obj: Assignment, callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    current_leader_tag = callback.from_user.username
    other_leaders = select_leader_with_same_subject(assignment_obj.subject_id, current_leader_tag)

    if other_leaders:
        await state.update_data(assignment_obj=assignment_obj)

        for leader in other_leaders:
            leader_chat_id = leader[0]
            leader_id_str = str(leader[2])
            leader_name_str = str(leader[1])

            kb.add(
                InlineKeyboardButton(text=f"Поделиться со старостой {leader_name_str}", callback_data=leader_id_str)
            )

            await state.set_state(AddAssignment.share_with_other_leader)
    else:
        await state.set_state(AddAssignment.real_finish)
    kb.adjust(1)
    return kb


def schedule_reminders(bot: Bot, scheduler):
    assignment_obj_list = select_all_fresh_assignments()
    for assignment_obj in assignment_obj_list:
        deadline = assignment_obj.deadline.dttm
        reminder_time = deadline - datetime.timedelta(days=1)

        scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[bot, assignment_obj])


async def send_reminder(bot: Bot, assignment_obj: Assignment):
    assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)
    reminder_text = f"Напоминание, до дедлайна 1 день\n {assignment_text}"
    await send_notification_to_group(bot, assignment_obj.group_id, reminder_text)
