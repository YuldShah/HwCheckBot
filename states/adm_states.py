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
    chat_link = State()  # Added for two-step chat link input
    confirm = State()
    del_con = State()    # For deletion confirmation
    reset_con = State()  # For reset all confirmation
    
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
    viewing_all = State()  # For viewing all submissions
    viewing_by_user = State()  # For viewing submissions by user
    viewing_by_exam = State()  # For viewing submissions by exam
    select_user = State()  # For selecting a user
    select_exam = State()  # For selecting an exam