import asyncio
import datetime
import logging
import sys

from aiogram import Dispatcher, types, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from days_of_week import days_of_week
from misc import *
from states import *

from db import *

TEST_TOKEN = "6570387436:AAF97uK9eF23S4GByAv3bOq0HEGQT_sd67o"
MAIN_TOKEN = '7057080247:AAF7lvvtHip5Eynij5FV4g3w4vDP6LMqH1I'

dp = Dispatcher()


@dp.message(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    kb = create_kb()
    if check_student_in_db(message.from_user.id):
        kb.add(
            InlineKeyboardButton(text="Посмотреть ДЗ", callback_data="Check assignments"),
        )
        if is_leader(message.from_user.username):
            # kb.add(InlineKeyboardButton(text="Удалить ДЗ", callback_data="Delete assignment"))
            kb.add(
                InlineKeyboardButton(text="Добавить ДЗ", callback_data="Add assignment"),
                InlineKeyboardButton(text="Изменить ДЗ / Поделиться с другим старостой",
                                     callback_data="Edit assignment"),
                InlineKeyboardButton(text="ДЗ от других старост", callback_data="Assignments from other leaders"),
            )
        if message.from_user.id == 816831722:
            kb.add(
                InlineKeyboardButton(text="Выгрузить логи", callback_data="Send logs"),
                InlineKeyboardButton(text="Написать старостам", callback_data="Send message to leaders"),
                InlineKeyboardButton(text="Написать всем", callback_data="Send message to all"),
            )
        print(message.from_user.username)
        kb.adjust(1)
        await message.answer("Выберите действие", reply_markup=kb.as_markup())
        await state.set_state(StartState.start)
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
@dp.callback_query(F.data == "back", EditAssignment.choose_deadline)
@dp.callback_query(F.data == "back", AssignmentsFromOtherLeaders.select_assignment)
async def start_command(callback: CallbackQuery, state: FSMContext):
    print("start")
    kb = create_kb()
    name = callback.from_user.first_name
    if check_student_in_db(callback.from_user.id):
        print("Чел зареган")
        kb.add(
            InlineKeyboardButton(text="Посмотреть ДЗ", callback_data="Check assignments"),
        )
        if is_leader(callback.from_user.username):
            # kb.add(InlineKeyboardButton(text="Удалить ДЗ", callback_data="Delete assignment"))
            kb.add(
                InlineKeyboardButton(text="Добавить ДЗ", callback_data="Add assignment"),
                InlineKeyboardButton(text="Изменить ДЗ / Поделиться с другим старостой", callback_data="Edit assignment"),
                InlineKeyboardButton(text="ДЗ от других старост", callback_data="Assignments from other leaders")
            )
        if callback.from_user.id == 816831722:
            kb.add(
                InlineKeyboardButton(text="Выгрузить логи", callback_data="Send logs"),
                InlineKeyboardButton(text="Написать старостам", callback_data="Send message to leaders"),
                InlineKeyboardButton(text="Написать всем", callback_data="Send message to all"),
            )
        kb.adjust(1)
        await callback.message.answer(f"Привет, {name}, Выберите действие", reply_markup=kb.as_markup())
        await state.set_state(StartState.start)
    else:
        print("Чел не зареган")
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
    kb.add(
        InlineKeyboardButton(text="Общая сводка", callback_data="overall")
    )

    group_id = select_group_id_by_chat_id(callback.from_user.id)
    await state.update_data(group_id=group_id)

    subjects_by_group = select_subjects_by_group_id(group_id)
    for subject in subjects_by_group:
        kb.add(
            InlineKeyboardButton(text=subject[1], callback_data=f"{subject[0]}")
        )
    kb.adjust(1)
    await callback.message.answer(text="Как посмотреть домашку?", reply_markup=kb.as_markup())
    await state.set_state(CheckAssignment.start)


@dp.callback_query(CheckAssignment.start)
async def check_assignments_start(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    result_assignment_text = ""
    chat_id = callback.from_user.id
    data = await state.get_data()
    group_id = data['group_id']
    if callback.data == "overall":
        assignments_list = select_assignments_by_group_id(group_id)
    else:
        subject_id = int(callback.data)
        assignments_list = select_assignments_by_group_id_and_subject_id(group_id, subject_id)
    for assignment in assignments_list:
        assignment_text = create_assignment_text(
            assignment.subject,
            assignment.deadline.string,
            assignment.description,
            assignment.deadline.day_of_week,
            assignment.deadline.days_remaining
        )

        result_assignment_text += assignment_text
    if result_assignment_text != "":
        await callback.message.answer(text=result_assignment_text, reply_markup=kb.as_markup())
    else:
        await callback.message.answer(text="Домашек пока нет", reply_markup=kb.as_markup())
    await state.set_state(CheckAssignment.start)


@dp.callback_query(F.data == "Add assignment")
@dp.callback_query(F.data == "back", AddAssignment.choose_deadline)
async def add_assignment_start(callback: CallbackQuery, state: FSMContext):
    await choose_subject(callback, state)
    await state.set_state(AddAssignment.start)


@dp.callback_query(F.data != "back", AddAssignment.start)
@dp.callback_query(F.data == "back", AddAssignment.input_description)
async def add_assignment_choose_deadline(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    if callback.data != "back":
        subject_id = int(callback.data)
        await state.update_data(subject_id=subject_id)

    await callback.message.answer(
        text="Введите дедлайн в формате dd.mm \n\nНапример, 10.09",
        reply_markup=kb.as_markup()
    )
    await state.set_state(AddAssignment.choose_deadline)


@dp.message(AddAssignment.choose_deadline)
async def add_assignment_input_description(message: Message, state: FSMContext):
    kb = create_kb()
    try:
        date_str = message.text
        parsed_date = string_to_dttm(date_str)
        deadline = Deadline(parsed_date)

        await message.answer(text="Введите описание ДЗ", reply_markup=kb.as_markup())
        await state.update_data(deadline=deadline)
        await state.set_state(AddAssignment.input_description)
    except ValueError:
        await message.answer(text="Некорректный ввод даты, попробуйте ввести в формате 'дд.мм'")


@dp.callback_query(F.data == "back", AddAssignment.finish)
async def add_assignment_input_description(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    await callback.message.answer(text="Введите описание ДЗ", reply_markup=kb.as_markup())
    await state.set_state(AddAssignment.input_description)


@dp.message(AddAssignment.input_description)
async def add_assignment_accept_dz(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)

    kb, result_str = await add_assignment_accept_dz_logic(description, state)

    await message.answer(text=result_str, reply_markup=kb.as_markup())
    await state.set_state(AddAssignment.finish)


@dp.callback_query(F.data == "back", AddAssignment.real_finish)
async def add_assignment_accept_dz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    description = data['description']

    kb, result_str = add_assignment_accept_dz_logic(description, state)

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

    assignment_id = insert_assignment(subject_id, group_id, description, deadline)
    assignment_obj = select_assignment_by_id(assignment_id)
    assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)

    kb = await share_assignment_start_logic(assignment_obj=assignment_obj, callback=callback, state=state)

    await send_add_assignment_notification_to_group(bot, group_id, assignment_text)

    await callback.message.answer(text="ДЗ создано\n\nДля перехода в начало нажите /start", reply_markup=kb.as_markup())


@dp.callback_query(AddAssignment.share_with_other_leader)
async def add_assignment_share_with_other_leader(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assignment_obj: Assignment = data['assignment_obj']
    leader_id = callback.data
    sender_id = select_leader_id_by_chat_id(callback.from_user.id)
    print(f"leader_id: {leader_id}")
    leader_chat_id = data['leader_chat_id']
    try:
        insert_shared_assignment_to_queue(
            sender_id=sender_id,
            receiver_id=int(leader_id),
            assignment_id=assignment_obj.id,
        )
        await callback.message.answer(text="Отправлено,\n\nДля перехода в начало нажите /start")
        await bot.send_message(
            chat_id=leader_chat_id,
            text=f"{callback.from_user.username} предлагает вам добавить домашку для вашей группы\n\n"
                 f"Доделайте свои дела и нажмите /shared_assignments чтобы посмотреть ее",
        )
    except Exception as e:
        print(f"Ошибка при отправке домашки в функции add_assignment_share_with_other_leader: {e}")


@dp.callback_query(F.data == "Edit assignment")
@dp.callback_query(EditAssignment.edit_assignment, F.data == "back")
async def edit_assignment_start(callback: CallbackQuery, state: FSMContext):
    await choose_subject(callback, state)
    await state.set_state(EditAssignment.choose_deadline)


@dp.callback_query(EditAssignment.choose_deadline)
@dp.callback_query(EditAssignment.choose_action, F.data == "back")
async def edit_assignment_choose_deadline(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    data = await state.get_data()
    if callback.data != "back":
        subject_id = int(callback.data)
        await state.update_data(subject_id=subject_id)
    else:
        subject_id = int(data['group_id'])
    group_id = int(data['group_id'])

    assignments = select_assignments_by_group_id_and_subject_id(group_id, subject_id)
    if assignments:
        await state.update_data(assignments=assignments)
        for assignment in assignments:
            kb.add(
                InlineKeyboardButton(
                    text=f"{assignment.deadline.string} {assignment.deadline.day_of_week}",
                    callback_data=str(assignment.id))
            )
        kb.adjust(1)
        await callback.message.answer(text="Какой дедлайн у задания?", reply_markup=kb.as_markup())
        await state.set_state(EditAssignment.edit_assignment)
    else:
        await callback.message.answer(text="ДЗ по этому предмету нет", reply_markup=kb.as_markup())


@dp.callback_query(EditAssignment.edit_assignment)
@dp.callback_query(EditAssignment.edit_description, F.data == "back")
async def edit_assignment_choose_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assignments = data['assignments']
    if callback.data != "back":
        assignment_id = int(callback.data)
        await state.update_data(assignment_id=assignment_id)
    else:
        assignment_id = data['assignment_id']
    selected_assignment: Assignment = find_by_id(assignments, assignment_id)

    await state.update_data(assignment=selected_assignment)

    kb = create_kb()
    kb.add(
        InlineKeyboardButton(text="📝 Изменить описание ДЗ", callback_data="edit description"),
        InlineKeyboardButton(text="🕔 Изменить дедлайн ДЗ", callback_data="edit deadline"),
        InlineKeyboardButton(text="✉️ Отправить ДЗ другому старосте", callback_data="share assignment"),
    )
    kb.adjust(1)
    await callback.message.answer(text=f"Вы выбрали дз по {selected_assignment.subject}, дедлайн в "
                                       f"{selected_assignment.deadline.string}\n\n Выберите действие",
                                  reply_markup=kb.as_markup())
    await state.set_state(EditAssignment.choose_action)


@dp.callback_query(EditAssignment.choose_action, F.data == "share assignment")
@dp.callback_query(EditAssignment.edit_description, F.data == "back")
async def edit_assignment_share_assignment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assignment_obj: Assignment = data["assignment"]
    for key in data.keys():
        print(f"{key}: {data[key]}")
    kb = await share_assignment_start_logic(
        assignment_obj=assignment_obj,
        callback=callback,
        state=state
    )
    await callback.message.answer("Выберите старосту", reply_markup=kb.as_markup())


@dp.callback_query(EditAssignment.choose_action, F.data == "edit description")
@dp.callback_query(EditAssignment.save_new_description, F.data == "back")
async def edit_assignment_edit_description(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    data = await state.get_data()
    assignment: Assignment = data['assignment']
    assignment_description = assignment.description

    await callback.message.answer(
        text=f"Текущее описание ДЗ:\n\n{assignment_description}\n\nВведите новое",
        reply_markup=kb.as_markup()
    )
    await state.set_state(EditAssignment.edit_description)


@dp.message(EditAssignment.edit_description)
@dp.message(EditAssignment.edit_deadline)
async def edit_assignment_edit_description_check_new_description(message: Message, state: FSMContext):
    kb = create_kb()
    kb.add(InlineKeyboardButton(text="Сохранить", callback_data="save"))

    data = await state.get_data()
    assignment = data['assignment']
    description = ''
    deadline_str = ""

    if await state.get_state() == "EditAssignment:edit_description":
        new_description = message.text
        description = new_description
        await state.update_data(new_description=new_description)
        deadline_str = assignment.deadline.string
        await state.set_state(EditAssignment.save_new_description)
    elif await state.get_state() == "EditAssignment:edit_deadline":
        date_str = message.text
        try:
            parsed_date = string_to_dttm(date_str)
            new_deadline = Deadline(parsed_date)
            deadline_str = new_deadline.string
            await state.update_data(new_deadline=new_deadline)
            description = assignment.description
            await state.set_state(EditAssignment.save_new_deadline)
        except Exception as e:
            print(e)
            await message.answer(text="Некорректный ввод даты, попробуйте ввести в формате 'дд.мм'")

    if description != "" and deadline_str != "":
        assignment_text = create_assignment_text(
            subject=assignment.subject,
            deadline_str=deadline_str,
            description=description,
            week_day=assignment.deadline.day_of_week,
            days_remaining=assignment.deadline.days_remaining,
        )
        await message.answer(
            text=f"ДЗ будет выглядеть следующим образом:\n\n{assignment_text}\n\nСохраняем?",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(text=f"что-то пошло не так")


@dp.callback_query(EditAssignment.save_new_description, F.data == "save")
@dp.callback_query(EditAssignment.save_new_deadline, F.data == "save")
async def edit_assignment_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assignment_id = data['assignment_id']
    if await state.get_state() == "EditAssignment:save_new_description":
        new_description = data['new_description']
        try:
            update_description_by_assignment_id(assignment_id, new_description)
            assignment_obj = select_assignment_by_id(assignment_id)
            assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)
            await send_edit_assignment_new_description_notification_to_group(
                bot=bot,
                group_id=assignment_obj.group_id,
                assignment_text=assignment_text
            )
            await callback.message.answer(text="ДЗ обновлено\n\nНажмите /start для перехода в начало")
        except Exception as e:
            print(f"Ошибка при обновлении дз: {e}")
            await callback.message.answer(text="Что-то пошло не так")
    elif await state.get_state() == "EditAssignment:save_new_deadline":
        new_deadline = data['new_deadline']
        try:
            update_deadline_by_assignment_id(assignment_id, new_deadline)
            assignment_obj = select_assignment_by_id(assignment_id)
            assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)
            await send_edit_assignment_new_deadline_notification_to_group(
                bot=bot,
                group_id=assignment_obj.group_id,
                assignment_text=assignment_text
            )
            await callback.message.answer(text="ДЗ обновлено\n\nНажмите /start для перехода в начало")
        except Exception as e:
            print(f"Ошибка при обновлении дз: {e}")
            await callback.message.answer(text="Что-то пошло не так")


@dp.callback_query(EditAssignment.choose_action, F.data == "edit deadline")
# @dp.callback_query(EditAssignment.save_new_description, F.data == "back")
async def edit_assignment_edit_deadline(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    data = await state.get_data()
    assignment: Assignment = data['assignment']
    assignment_deadline = assignment.deadline.string

    await callback.message.answer(
        text=f"Текущий дедлайн ДЗ:\n\n{assignment_deadline}\n\nВведите новый в формате дд.мм",
        reply_markup=kb.as_markup()
    )
    await state.set_state(EditAssignment.edit_deadline)


@dp.callback_query(F.data == "Assignments from other leaders")
async def check_assignments_from_other_leaders_start(callback: CallbackQuery, state: FSMContext):
    kb = create_kb()
    waiting_assignments = fetch_assignments_queue(receiver_id=callback.from_user.id)
    for assignment in waiting_assignments:
        kb_text = f"ДЗ от старосты {assignment[1]}"
        kb.add(InlineKeyboardButton(text=kb_text, callback_data=f"{assignment[0]} | {assignment[2]}"))
    kb.adjust(1)
    await callback.message.answer(text="Выберите ДЗ", reply_markup=kb.as_markup())
    await state.set_state(AssignmentsFromOtherLeaders.select_assignment)


@dp.message(Command("shared_assignments"))
async def check_assignments_from_other_leaders_start(message: Message, state: FSMContext):
    kb = create_kb()
    waiting_assignments = fetch_assignments_queue(receiver_id=message.from_user.id)
    for assignment in waiting_assignments:
        kb_text = f"ДЗ от старосты {assignment[1]}"
        kb.add(InlineKeyboardButton(text=kb_text, callback_data=f"{assignment[0]} | {assignment[3]}"))
    kb.adjust(1)
    await message.answer(text="Выберите ДЗ", reply_markup=kb.as_markup())
    await state.set_state(AssignmentsFromOtherLeaders.select_assignment)


@dp.callback_query(AssignmentsFromOtherLeaders.select_assignment)
async def check_assignments_from_other_leaders_accept(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("|")
    assignment_id = int(callback_data[0])
    shared_assignment_id = callback_data[1]
    assignment_obj = select_assignment_by_id(assignment_id)
    await state.update_data(
        assignment_obj=assignment_obj,
        shared_assignment_id=shared_assignment_id
    )
    assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)

    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="Принять", callback_data=f"share_assignment_accept"),
        InlineKeyboardButton(text="Отклонить", callback_data="share assignment|cancel"),
    )

    await callback.message.answer(text=f"Описание ДЗ:\n\n{assignment_text}\n\nПринимаем?", reply_markup=kb.as_markup())
    await state.set_state(AssignmentsFromOtherLeaders.accept)


@dp.callback_query(AssignmentsFromOtherLeaders.accept, F.data == "share_assignment_accept")
async def accept_shared_assignment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    assignment_obj = data['assignment_obj']
    assignment_text = create_assignment_text_from_assignment_obj(assignment_obj)
    shared_assignment_id = data["shared_assignment_id"]
    group_id = select_group_id_by_chat_id(callback.from_user.id)
    try:
        insert_assignment(
            subject_id=assignment_obj.subject_id,
            group_id=group_id,
            description=assignment_obj.description,
            deadline=assignment_obj.deadline,
        )
        update_assignments_queue(shared_assignment_id)
        await send_add_assignment_notification_to_group(bot, group_id, assignment_text)
        await callback.message.answer(text="ДЗ добавлено успешно\n\nДля перехода в начало нажите /start")
    except Exception as e:
        print(f"Ошибка при добавлении домашки {e}")
        await callback.message.answer(text="Что-то пошло не так")


@dp.callback_query(F.data == "Send logs")
async def send_logs(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer_document(FSInputFile("nohup.out"))


@dp.callback_query(F.data == "Send message to leaders")
async def send_message_to_leaders_input_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сообщение для старост")
    await state.set_state(SendMessage.input_message_to_leaders)


@dp.message(SendMessage.input_message_to_leaders)
async def send_message_to_leaders_send_message(message: Message, state: FSMContext):
    db_leaders = select_leaders()
    for leader in db_leaders:
        leader_chat_id = leader[2]
        await bot.send_message(chat_id=leader_chat_id, text=f"Привет, старосты,\n\n {message.text}")
    await message.answer(text="Сообщение отправлено, нажмите /start")


@dp.callback_query(F.data == "Send message to all")
async def send_message_to_all_input_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сообщение для всех")
    await state.set_state(SendMessage.input_message_to_all)


@dp.message(SendMessage.input_message_to_all)
async def send_message_to_all_send_message(message: Message, state: FSMContext):
    db_leaders = select_leaders()
    for leader in db_leaders:
        leader_chat_id = leader[2]
        await bot.send_message(chat_id=leader_chat_id, text=f"Всем привет,\n\n {message.text}")
    await message.answer(text="Сообщение отправлено, нажмите /start")


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
