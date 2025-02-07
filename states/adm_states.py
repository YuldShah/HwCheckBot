from aiogram.fsm.state import State, StatesGroup

class mands(StatesGroup):
    mmenu = State()
    title = State()
    link = State()
    confirm = State()

class dels(StatesGroup):
    confirm = State()

class sets(StatesGroup):
    smenu = State()
    ping = State()

class accstates(StatesGroup):
    acmenu = State()
    post = State()
    link = State()
    confirm = State()
    fmans = State()
    del_con = State()
    manl = State()

class creates(StatesGroup):
    title = State()
    about = State()
    instructions = State()  # New state added
    number = State()
    way = State()
    ans = State()

class edits(StatesGroup):
    emenu = State()
    edit = State()
    title = State()
    about = State()
    edans = State()
    share = State()
    post = State()