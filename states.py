from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class SomeState(StatesGroup):
    start = State()


class Registration(StatesGroup):
    register = State()


class CheckAssignment(StatesGroup):
    start = State()


class AddAssignment(StatesGroup):
    start = State()
    choose_deadline = State()
    input_description = State()
    finish = State()
    real_finish = State()


class StartState(StatesGroup):
    start_state = State()