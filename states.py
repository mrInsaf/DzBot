from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class StartState(StatesGroup):
    start = State()


class Registration(StatesGroup):
    register = State()


class CheckAssignment(StatesGroup):
    start = State()
    choose_subject = State()


class AddAssignment(StatesGroup):
    start = State()
    choose_groups = State()
    choose_deadline = State()
    input_description = State()
    finish = State()
    share_with_other_leader = State()
    real_finish = State()


class EditAssignment(StatesGroup):
    start = State()
    choose_subject = State()
    choose_deadline = State()
    edit_assignment = State()
    choose_action = State()
    edit_description = State()
    edit_deadline = State()
    save_new_description = State()
    save_new_deadline = State()

