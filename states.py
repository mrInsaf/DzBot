from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class Keyboard(StatesGroup):
    keyboard = State()

class StartState(StatesGroup):
    start_state = State()