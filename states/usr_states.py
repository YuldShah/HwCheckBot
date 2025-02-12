from aiogram.fsm.state import StatesGroup, State

class check_hw_states(StatesGroup):
    answer = State()
    confirm = State()