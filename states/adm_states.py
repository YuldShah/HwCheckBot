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
    defs = State()
    ping = State()

class accstates(StatesGroup):
    acmenu = State()
    post = State()
    link = State()
    confirm = State()
    fmans = State()
    del_con = State()
    
    manl = State()
    adda = State()
    rema = State()
    confirm_add = State()
    confirm_del = State()

class creates(StatesGroup):
    title = State()
    about = State()
    instructions = State() 
    attachments = State()
    number = State()
    sdate = State()
    # duration = State()
    way = State()
    ans = State()
    setts = State()
    folder_change = State()
    confirm = State()

class arch_states(StatesGroup):
    folders = State()
    fol_title = State()
    tests = State()
    rdis = State()
    folder_change = State()
    rmfconfirm = State()
    emenu = State()
    edit = State()
    title = State() #for title 
    about = State() #for description
    instruc = State() #for instructions
    edans = State() #to change answers 
    attaches = State() # to change attachments
    share = State() 
    post = State() 
    rmtconfirm = State()
    sdate = State() #for deadline  

class statsstates(StatesGroup):
    stmenu = State()