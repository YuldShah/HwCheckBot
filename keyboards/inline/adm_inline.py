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
        InlineKeyboardButton(text=dict.post, callback_data="post"), 
        InlineKeyboardButton(text=dict.defaults, callback_data="defaults")
    ],
    [
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

def obom(cur, numq, donel, mcqnum=config.MULTIPLE_CHOICE_DEF, page=1):
    """
    cur: current question number
    numq: total number of questions
    mcqnum: number of choices in mcq
    donel: list of done questions
    page: current page, self explanatory
    """
    
    btns = []
    arow = [InlineKeyboardButton(text="-", callback_data="test_minus")]
    for i in range(mcqnum):
        arow.append(InlineKeyboardButton(text=f"{chr(65+i)}", callback_data=f"mcq_{i-65}")) # add ✓ for multiple answers and maybe done button
    # arow.append(*[InlineKeyboardButton(text=f"{chr(65+i)}", callback_data=f"mcq_{i-65}") for i in range(config.MULTIPLE_CHOICE_DEF)])
    arow.append(InlineKeyboardButton(text="+", callback_data="test_plus"))
    btns.append(arow)
    qforthis = min(config.MAX_QUESTION_IN_A_PAGE, numq-(page-1)*config.MAX_QUESTION_IN_A_PAGE)
    for i in range((qforthis+4)//5):
        row = []
        for j in range(min(5, qforthis-i*5)):
            now = (page-1)*config.MAX_QUESTION_IN_A_PAGE+i*5+j+1
            if now == cur:
                row.append(InlineKeyboardButton(text=f"🟡 {now}", callback_data=f"jump_{now}"))
            elif now in donel:
                row.append(InlineKeyboardButton(text=f"🟢 {now}", callback_data=f"jump_{now}"))
            else:
                row.append(InlineKeyboardButton(text=f"{now}", callback_data=f"jump_{now}"))
        btns.append(row)
    row = [
        InlineKeyboardButton(text="⇐", callback_data="test_prev"),
        InlineKeyboardButton(text="←", callback_data="test_back"),
        InlineKeyboardButton(text=f"{page}", callback_data="test_page"),
        InlineKeyboardButton(text="→", callback_data="test_next"),
        InlineKeyboardButton(text="⇒", callback_data="test_next")
    ]
    btns.append(row)
    return InlineKeyboardMarkup(inline_keyboard=btns)


btns4 = [
    [
        InlineKeyboardButton(text="Fetch data", callback_data="fetch_data"),
        InlineKeyboardButton(text="Cancel", callback_data="cancel_perm")
    ]
]
perm_inl = InlineKeyboardMarkup(inline_keyboard=btns4)

def grant_perm_to(userid, mention):
    btns = [
        [
            InlineKeyboardButton(text="Grant permission", callback_data=f"grant_{userid}_{mention}")
        ],
        [
            InlineKeyboardButton(text="Cancel", callback_data="cancel_perm")
        ]
    ]


btns5 = [
    [
        InlineKeyboardButton(text="Go to bot", url=f"https://t.me/{config.bot_info.username}")
    ]
]

goto_bot = InlineKeyboardMarkup(inline_keyboard=btns5)