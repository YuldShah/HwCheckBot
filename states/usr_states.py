from aiogram.fsm.state import StatesGroup, State

class check_hw_states(StatesGroup):
    details = State()
    way = State()
    answer = State()
    confirm = State()