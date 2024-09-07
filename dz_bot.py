import asyncio
import logging
import sys

from aiogram import Dispatcher, types, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from misc import *
from states import *

from db import *

TEST_TOKEN = "6570387436:AAF97uK9eF23S4GByAv3bOq0HEGQT_sd67o"
MAIN_TOKEN = '7129795991:AAHb793O24B1UvI0c-TlGQ-m_e1zDFM0x08'

dp = Dispatcher()


@dp.message(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    print("start")
    kb = create_kb()
    if check_student_in_db(message.from_user.id):
        kb.add(
            InlineKeyboardButton(text="Посмотреть ДЗ", callback_data="Check assignments"),
            InlineKeyboardButton(text="Добавить ДЗ", callback_data="Add assignment"),
        )
        kb.adjust(1)
        await message.answer("Выберите действие", reply_markup=kb.as_markup())
    else:
        groups = select_all_groups()
        username = message.from_user.username
        for group in groups:
            kb.add(
                InlineKeyboardButton(text=group[1], callback_data=str(group[0]))
            )
            kb.adjust(1)
        await message.answer(text=f"Привет {username} Выберите группу", reply_markup=kb.as_markup())
        await state.set_state(Registration.register)


@dp.callback_query(F.data == "back", AddAssignment.start)
@dp.callback_query(F.data == "back", CheckAssignment.start)
async def start_command(callback: CallbackQuery, state: FSMContext):
    print("start")
    kb = create_kb()
    name = callback.from_user.first_name
    if check_student_in_db(callback.message.from_user.id):
        kb.add(
            InlineKeyboardButton(text="Посмотреть ДЗ", callback_data="Check assignments"),
            InlineKeyboardButton(text="Добавить ДЗ", callback_data="Add assignment"),
        )
        kb.adjust(1)
        await callback.message.answer(f"Привет, {name}, Выберите действие", reply_markup=kb.as_markup())
    else:
        groups = select_all_groups()
        for group in groups:
            kb.add(
                InlineKeyboardButton(text=group[1], callback_data=str(group[0]))
            )
            kb.adjust(1)
        await callback.message.answer(text=f"Привет, {name}, Выберите группу", reply_markup=kb.as_markup())
        await state.set_state(Registration.register)


@dp.callback_query(Registration.register)
async def register_student(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data)
    insert_student(
        chat_id=callback.from_user.id,
        name=callback.from_user.first_name,
        tag=callback.from_user.username,
        group_id=group_id
    )
    await start_command(callback, state)


@dp.callback_query(F.data == "Check assignments")
async def check_assignments_start(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    result_assignment_text = ""
    chat_id = callback.from_user.id
    group_id = select_group_id_by_chat_id(chat_id)
    await state.update_data(group_id=group_id)
    assignments_raw = select_assignments_by_group_id(group_id)
    for assignment in assignments_raw:
        subject = assignment[0]
        deadline = assignment[1].strftime('%d.%m.%Y %H:%M')
        description = assignment[2]
        assignment_text = create_assignment_text(subject, deadline, description)
        result_assignment_text += assignment_text
    await callback.message.answer(text=result_assignment_text, reply_markup=kb.as_markup())
    await state.set_state(CheckAssignment.start)


@dp.callback_query(F.data == "Add assignment")
@dp.callback_query(F.data == "back", AddAssignment.choose_deadline)
async def add_assignment_start(callback: CallbackQuery, state: FSMContext):
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
    await state.set_state(AddAssignment.start)


@dp.callback_query(F.data != "back", AddAssignment.start)
@dp.callback_query(F.data == "back", AddAssignment.input_description)
async def add_assignment_choose_deadline(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    if callback.data != "back":
        subject_id = int(callback.data)
        await state.update_data(subject_id=subject_id)

    await callback.message.answer(
        text="Введите дедлайн в формате dd.mm.YYYY H:M\n\nНапример, 10.09.2024 18:00",
        reply_markup=kb.as_markup()
    )
    await state.set_state(AddAssignment.choose_deadline)


@dp.message(AddAssignment.choose_deadline)
async def add_assignment_input_description(message: Message, state: FSMContext):
    kb = create_kb()
    try:
        date_str = message.text
        date_format = "%d.%m.%Y %H:%M"

        # Парсинг строки в объект datetime
        parsed_date = datetime.datetime.strptime(date_str, date_format)
        await message.answer(text="Введите описание ДЗ", reply_markup=kb.as_markup())
        await state.update_data(deadline=parsed_date)
        await state.set_state(AddAssignment.input_description)
    except Exception as e:
        await message.answer(text="Некорректный ввод, попробуйте еще раз")


@dp.callback_query(F.data == "back", AddAssignment.finish)
async def add_assignment_input_description(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    await callback.message.answer(text="Введите описание ДЗ", reply_markup=kb.as_markup())
    await state.set_state(AddAssignment.input_description)


@dp.message(AddAssignment.input_description)
async def add_assignment_accept_dz(message: Message, state: FSMContext):
    kb = create_kb()
    kb.add(InlineKeyboardButton(text="Все верно", callback_data="accept"))
    kb.adjust(2)

    data = await state.get_data()
    result_str = "Проверьте правильность заполнения дз: \n"

    subject_id = data['subject_id']
    subject = select_subject_by_subject_id(subject_id)
    deadline = data['deadline'].strftime("%d.%m.%Y %H:%M")
    description = message.text
    await state.update_data(description=description)

    assignment_text = create_assignment_text(subject, deadline, description)
    result_str += assignment_text
    await message.answer(text=result_str, reply_markup=kb.as_markup())
    await state.set_state(AddAssignment.finish)


@dp.callback_query(F.data == "back", AddAssignment.real_finish)
async def add_assignment_accept_dz(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    kb.add(InlineKeyboardButton(text="Все верно", callback_data="accept"))
    kb.adjust(2)

    data = await state.get_data()
    result_str = "Проверьте правильность заполнения дз: \n"

    subject_id = data['subject_id']
    subject = select_subject_by_subject_id(subject_id)
    deadline = data['deadline'].strftime("%d.%m.%Y %H:%M")
    description = data['description']

    assignment_text = create_assignment_text(subject, deadline, description)
    result_str += assignment_text
    await callback.message.answer(text=result_str, reply_markup=kb.as_markup())
    await state.set_state(AddAssignment.finish)


@dp.callback_query(F.data == "accept", AddAssignment.finish)
async def add_assignment_finish(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(f'data is: {data}')
    subject_id = data['subject_id']
    group_id = data['group_id']
    description = data['description']
    deadline = data['deadline']

    insert_assignment(subject_id, group_id, description, deadline)
    await callback.message.answer(text="ДЗ создано\n\nДля перехода в начало нажите /start")
    await state.set_state(AddAssignment.real_finish)


async def main(token: str) -> None:
    global bot
    if token == "test":
        bot = Bot(
            TEST_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
            )
        )
        await dp.start_polling(bot)
    else:
        bot = Bot(
            MAIN_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
            )
        )
        await dp.start_polling(bot)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <token>")
    else:
        try:
            TOKEN = sys.argv[1]
            asyncio.run(main(TOKEN))
        except Exception as e:
            logging.exception(f"Произошла ошибка: {e}")
            print(f"Произошла ошибка: {e}")
