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
        arow = []
        for i in range(typesl[current-1]):
            arow.append(InlineKeyboardButton(text="🟢" if chr(65+i)==answers[current-1] else chr(65+i), callback_data=f"mcq_{chr(65+i)}"))
        btns.append(arow)
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
    allp = (total+config.MAX_QUESTION_IN_A_PAGE-1)//config.MAX_QUESTION_IN_A_PAGE
    if allp==1:
        return InlineKeyboardMarkup(inline_keyboard=btns)
    row = [
        InlineKeyboardButton(text="⇐", callback_data="page_prev"),
        InlineKeyboardButton(text=f"Bet: {page}/{allp}", callback_data="page_now"),
        InlineKeyboardButton(text="⇒", callback_data="page_next")
    ]
    btns.append(row)
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns1 = [
    [
        InlineKeyboardButton(text="🖋 Adminga yozish", url=config.ADMIN_URL)
    ]
]

elbek = InlineKeyboardMarkup(inline_keyboard=btns1)

btns2 = [
    [
        InlineKeyboardButton(text=dict.start_test, callback_data="start_test")
    ]
]
lets_start = InlineKeyboardMarkup(inline_keyboard=btns2)

btns3 = [
    [
        InlineKeyboardButton(text=dict.all_at_once_uz, callback_data="all"),
        InlineKeyboardButton(text=dict.one_by_one_uz, callback_data="one")
    ]
]
ans_enter_method_usr = InlineKeyboardMarkup(inline_keyboard=btns3)

btns4 = [
    [
        InlineKeyboardButton(text=dict.back_uz, callback_data="back"),
        InlineKeyboardButton(text=dict.send_uz, callback_data="submit")    
    ]
]
submit_ans_user = InlineKeyboardMarkup(inline_keyboard=btns4)

def share_sub_usr(code):
    btns = [
        [
            InlineKeyboardButton(text=dict.share_uz, switch_inline_query=f"sub_{code}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)


def results_time(subid, ccode, vis):
    btns = [
        [
            InlineKeyboardButton(text=dict.share_uz, switch_inline_query=f"sub_{ccode}")
        ],
        [
            InlineKeyboardButton(text=dict.earlier, callback_data=f"result_earlier_{subid}"),
            InlineKeyboardButton(text=dict.later, callback_data=f"result_later_{subid}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns5 = [
    [
        InlineKeyboardButton(text=dict.continue_uz, callback_data="continue")
    ]
]
all_continue_usr = InlineKeyboardMarkup(inline_keyboard=btns5)

def get_missing_exams(exams):
    btns = []
    for title, idx in exams:
        btns.append([InlineKeyboardButton(text=title, callback_data=f"mexam_{idx}")])
    btns.append([InlineKeyboardButton(text=dict.back_uz, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)