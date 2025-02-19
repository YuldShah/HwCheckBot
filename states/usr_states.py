from aiogram.fsm.state import StatesGroup, State

class check_hw_states(StatesGroup):
    details = State()
    way = State()
    answer = State()
    confirm = State()

class result_states(StatesGroup):
    show = State()

class missing_hw_states(StatesGroup):
    exams = State()
    details = State()
    way = State()
    answer = State()
    confirm = State()