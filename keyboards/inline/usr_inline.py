from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat
from data.dict import check_subs
from data import config

def mand_chans(channels) -> InlineKeyboardMarkup:
    btns = []
    for name, idx, url in channels:
        btns.append([InlineKeyboardButton(text=name, url=url)])
    btns.append([InlineKeyboardButton(text=check_subs, callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def create_mcq_keyboard(cur: int, total: int, answers: list, types: list, page: int = 1) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard for user MCQ answering.
    cur: current question number
    total: total number of questions
    answers: list of user's answers (or None)
    types: list of number of options for each question (non-zero for MCQ, 0 for open-ended)
    """
    num_options = types[cur-1]
    option_buttons = []
    for i in range(num_options):
        letter = chr(65+i)
        btn_text = f"{letter}" if answers[cur-1] != letter else f"✔{letter}"
        option_buttons.append(InlineKeyboardButton(text=btn_text, callback_data=f"user_mcq_{letter}"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[option_buttons])
    # nav_row = []
    # if cur > 1:
    #     nav_row.append(InlineKeyboardButton(text="Prev", callback_data="user_prev"))
    # if cur < total:
    #     nav_row.append(InlineKeyboardButton(text="Next", callback_data="user_next"))
    # if nav_row:
    #     keyboard.append(*nav_row)
    return keyboard

btns1 = [
    [
        InlineKeyboardButton(text="🖋 Adminga yozish", url=config.ADMIN_URL)
    ]
]

elbek = InlineKeyboardMarkup(inline_keyboard=btns1)