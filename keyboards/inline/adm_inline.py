from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data import dict, config


def mandchans(channels = []):
    # channels = db.fetchall("SELECT title, link FROM channels")
    btns = []
    for channel in channels:
        btns.append([
                InlineKeyboardButton(text=channel[0], url=channel[1]),
                InlineKeyboardButton(text=dict.delete, callback_data=f"delete_{channel[2]}")
            ])
    btns.append([InlineKeyboardButton(text=dict.add_chat, callback_data="add_chat")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def mandconfirm(channel):
    btns = [
        [
            InlineKeyboardButton(text=channel[0], url=channel[1])
        ],
        [
            InlineKeyboardButton(text=dict.cancel, callback_data="cancel"),
            InlineKeyboardButton(text=dict.confirm, callback_data="confirm")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns1 = [
    [
        InlineKeyboardButton(text=dict.defaults, callback_data="defaults"),
        InlineKeyboardButton(text=dict.ping, callback_data="ping")
    ]
]
set_menu = InlineKeyboardMarkup(inline_keyboard=btns1)

def post_chan(channel):
    btns = []
    if channel:
        btns.append([InlineKeyboardButton(text=channel[0], url=channel[1])])
        btns.append([InlineKeyboardButton(text=dict.reset, callback_data="reset")])
    btns.append([InlineKeyboardButton(text=dict.set_new, callback_data="set_new")])
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns2 = [
    [
        InlineKeyboardButton(text=dict.all_at_one, callback_data="all"),
        InlineKeyboardButton(text=dict.one_by_one, callback_data="one")
    ]
]
ans_enter_meth = InlineKeyboardMarkup(inline_keyboard=btns2)

btns3 = [
    [
        InlineKeyboardButton(text=dict.back, callback_data="back"),
        InlineKeyboardButton(text=dict.refresh_txt, callback_data="refresh_ping")
    ]
]
ping_set = InlineKeyboardMarkup(inline_keyboard=btns3)

def obom(cur, numq, donel, typesl, page=1):
    """
    cur: current question number
    numq: total number of questions
    donel: list of done questions
    typesl: list where each element is the number of options for that question (0 means open ended)
    page: current page
    """
    mode = 1 if typesl[cur-1] > 0 else 0
    btns = []
    if mode == 1:
        arow = [InlineKeyboardButton(text="-", callback_data="test_minus")]
        for i in range(typesl[cur-1]):
            if chr(65+i) == donel[cur-1]:
                arow.append(InlineKeyboardButton(text="🟢", callback_data=f"mcq_{chr(65+i)}"))
            else:
                arow.append(InlineKeyboardButton(text=f"{chr(65+i)}", callback_data=f"mcq_{chr(65+i)}"))
        arow.append(InlineKeyboardButton(text="+", callback_data="test_plus"))
        btns.append(arow)
        btns.append([InlineKeyboardButton(text=dict.switch_to_open, callback_data="switch_open")])
    else:
        btns.append([InlineKeyboardButton(text=dict.switch_to_mcq, callback_data="switch_mcq")])
    qforthis = min(config.MAX_QUESTION_IN_A_PAGE, numq - (page-1)*config.MAX_QUESTION_IN_A_PAGE)
    for i in range((qforthis+4)//5):
        row = []
        for j in range(min(5, qforthis - i*5)):
            now = (page-1)*config.MAX_QUESTION_IN_A_PAGE + i*5 + j + 1
            if now == cur:
                row.append(InlineKeyboardButton(text=f"🟡{now}", callback_data=f"jump_{now}"))
            elif donel[now-1]:
                row.append(InlineKeyboardButton(text=f"🟢{now}", callback_data=f"jump_{now}"))
            else:
                row.append(InlineKeyboardButton(text=f"🔴{now}", callback_data=f"jump_{now}"))
        btns.append(row)
    row = [
        InlineKeyboardButton(text="⇐", callback_data="page_prev"),
        InlineKeyboardButton(text=f"Pg: {page}/{(numq+config.MAX_QUESTION_IN_A_PAGE-1)//config.MAX_QUESTION_IN_A_PAGE}", callback_data="page_now"),
        InlineKeyboardButton(text="⇒", callback_data="page_next")
    ]
    btns.append(row)
    return InlineKeyboardMarkup(inline_keyboard=btns)


btns4 = [
    [
        InlineKeyboardButton(text="Ruxsat olish", callback_data="get_perm"),
    ]
]
perm_inl = InlineKeyboardMarkup(inline_keyboard=btns4)



def goto_bot(username):

    btns = [
        [
            InlineKeyboardButton(text="Go to bot", url=f"https://t.me/{username}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)


btns5 = [
    [
        InlineKeyboardButton(text=dict.post, callback_data="post"),
        InlineKeyboardButton(text=dict.manually, callback_data="manually")
    ]
]
access_menu = InlineKeyboardMarkup(inline_keyboard=btns5)

btns6 = [
    [
        InlineKeyboardButton(text=dict.add_access, callback_data="add_access"),
        InlineKeyboardButton(text=dict.del_access, callback_data="remove_access")
    ],
    [
        InlineKeyboardButton(text=dict.back, callback_data="back")
    ]
]
man_access = InlineKeyboardMarkup(inline_keyboard=btns6)

btns7 = [
    [
        InlineKeyboardButton(text=dict.today, callback_data="today"),
    ]
]
today = InlineKeyboardMarkup(inline_keyboard=btns7)

def ans_set_fin(visibility, resub, folder=None):
    btns = []
    if folder:
        btns.append([InlineKeyboardButton(text=dict.folder+folder, callback_data="folder")])
    btns.append([
            InlineKeyboardButton(text=dict.hide_not, callback_data=f"vis_on") if visibility else InlineKeyboardButton(text=dict.hide_ok, callback_data="vis_off")
        ])
    btns.append([
            InlineKeyboardButton(text=dict.resub_not, callback_data="resub_on") if resub else InlineKeyboardButton(text=dict.resub_ok, callback_data="resub_off")
        ])
    btns.append([InlineKeyboardButton(text=dict.contin, callback_data="continue")])
    return InlineKeyboardMarkup(inline_keyboard=btns)