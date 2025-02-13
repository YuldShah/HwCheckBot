from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat
from data.dict import check_subs
from data import config, dict

def mand_chans(channels) -> InlineKeyboardMarkup:
    btns = []
    for name, idx, url in channels:
        btns.append([InlineKeyboardButton(text=name, url=url)])
    btns.append([InlineKeyboardButton(text=check_subs, callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_answering_keys(current, total, answers, typesl, page=1, confirm=False) -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text=dict.continue_uz, callback_data="continue")]]
    if not confirm:
        btns = []
    if typesl[current-1] > 0: # MCQ
        for i in range(typesl[current-1]):
            btns.append([InlineKeyboardButton(text=chr(65+i), callback_data=f"mcq_{chr(65+i)}")])
    qforthis = min(config.MAX_QUESTION_IN_A_PAGE, total - (page-1)*config.MAX_QUESTION_IN_A_PAGE)
    for i in range((qforthis+4)//5):
        row = []
        for j in range(min(5, qforthis - i*5)):
            now = (page-1)*config.MAX_QUESTION_IN_A_PAGE + i*5 + j + 1
            if now == current:
                row.append(InlineKeyboardButton(text=f"🟡{now}", callback_data=f"jump_{now}"))
            elif answers[now-1]:
                row.append(InlineKeyboardButton(text=f"🟢{now}", callback_data=f"jump_{now}"))
            else:
                row.append(InlineKeyboardButton(text=f"🔴{now}", callback_data=f"jump_{now}"))
        btns.append(row)
    row = [
        InlineKeyboardButton(text="⇐", callback_data="page_prev"),
        InlineKeyboardButton(text=f"Bet: {page}/{(total+config.MAX_QUESTION_IN_A_PAGE-1)//config.MAX_QUESTION_IN_A_PAGE}", callback_data="page_now"),
        InlineKeyboardButton(text="⇒", callback_data="page_next")
    ]
    btns.append(row)


btns1 = [
    [
        InlineKeyboardButton(text="🖋 Adminga yozish", url=config.ADMIN_URL)
    ]
]

elbek = InlineKeyboardMarkup(inline_keyboard=btns1)