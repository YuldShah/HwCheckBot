from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat
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

def post_chan(channels=[]):
    btns = []
    for channel in channels:
        btns.append([
            InlineKeyboardButton(text=channel[0], url=channel[1]),
            InlineKeyboardButton(text=dict.delete, callback_data=f"delete_perm_{channel[2]}")
        ])
    btns.append([InlineKeyboardButton(text=dict.add_permit_chat, callback_data="add_perm_chat")])
    if channels:
        btns.append([InlineKeyboardButton(text=dict.reset, callback_data="reset")])
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

def obom(cur, numq, donel, typesl, page=1, confirm=False):
    """
    cur: current question number
    numq: total number of questions
    donel: list of done questions
    typesl: list where each element is the number of options for that question (0 means open ended)
    page: current page
    """
    mode = 1 if typesl[cur-1] > 0 else 0
    btns = []
    if confirm:
        btns.append([InlineKeyboardButton(text=dict.contin, callback_data="continue")])
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
    allp = (numq+config.MAX_QUESTION_IN_A_PAGE-1)//config.MAX_QUESTION_IN_A_PAGE
    if allp==1:
        return InlineKeyboardMarkup(inline_keyboard=btns)
    row = [
        InlineKeyboardButton(text="⇐", callback_data="page_prev"),
        InlineKeyboardButton(text=f"Pg: {page}/{allp}", callback_data="page_now"),
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
            InlineKeyboardButton(text="🤖 Botni ishga tushirish", url=f"https://t.me/{username}?start")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)


btns5 = [
    [
        InlineKeyboardButton(text=dict.post, callback_data="post"),
        InlineKeyboardButton(text=dict.manually, callback_data="manually")
    ],
    [
        InlineKeyboardButton(text="🔎 On inline mode", switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(query="allow", allow_user_chats=True))
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
    btns = [[InlineKeyboardButton(text=dict.back, callback_data="back"), InlineKeyboardButton(text=dict.finish, callback_data="continue")]]
    if folder:
        btns.append([InlineKeyboardButton(text=dict.folder+folder, callback_data="folder")])
    else:
        btns.append([InlineKeyboardButton(text=dict.folder_not, callback_data="folder")])
    btns.append([
            InlineKeyboardButton(text=dict.vis_cur_off, callback_data=f"vis_on") if not visibility else InlineKeyboardButton(text=dict.vis_cur_on, callback_data="vis_off")
        ])
    btns.append([
            InlineKeyboardButton(text=dict.resub_not, callback_data="resub_on") if not resub else InlineKeyboardButton(text=dict.resub_ok, callback_data="resub_off")
        ])
    # btns.append()
    return InlineKeyboardMarkup(inline_keyboard=btns)

def inl_folders(folders, curf):
    btns = []
    if curf:
        btns.append([InlineKeyboardButton(text=dict.folder_dont, callback_data="folder_0")])
    for idx, title in folders:
        btns.append([InlineKeyboardButton(text=("✅ " if idx == curf else "") + title, callback_data=f"folder_{idx}")])
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_create_folders(folders=[]):
    btns = [[InlineKeyboardButton(text=dict.null_folder, callback_data="fmng_0")]]
    for i, j in folders:
        btns.append([InlineKeyboardButton(text=j, callback_data=f"fmng_{i}")])
    arow = [InlineKeyboardButton(text=dict.add_folder, callback_data="add_folder")]
    if folders:
        arow.append(InlineKeyboardButton(text=dict.rm_folder, callback_data="rm_folder"))
    btns.append(arow)
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_folder_tests(tests, page=1):
    btns = []
    # If tests is empty, just return back button
    if not tests:
        btns.append([InlineKeyboardButton(text=dict.back, callback_data="back")])
        return InlineKeyboardMarkup(inline_keyboard=btns)
    
    # Sort tests by ID (newest to oldest)
    sorted_tests = sorted(tests, key=lambda x: x[0], reverse=True)
    
    # Pagination
    total_pages = max(1, (len(sorted_tests) + config.MAX_EXAMS_PER_PAGE - 1) // config.MAX_EXAMS_PER_PAGE)
    start_idx = (page - 1) * config.MAX_EXAMS_PER_PAGE
    end_idx = min(start_idx + config.MAX_EXAMS_PER_PAGE, len(sorted_tests))
    
    # Add test buttons for current page
    for i, j in sorted_tests[start_idx:end_idx]:
        btns.append([InlineKeyboardButton(text=j, callback_data=f"exman_{i}")])
    
    # Add pagination navigation if needed
    if total_pages > 1:
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data="tests_page_prev"))
        pagination_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="tests_page_now"))
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data="tests_page_next"))
        btns.append(pagination_row)
    
    # Always add back button
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def remove_att(attach_id):
    btns = [
        [
            InlineKeyboardButton(text=dict.unattach, callback_data=f"rma_{attach_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def edit_test_menu(visibility, resub):
    btns = [
        [
            InlineKeyboardButton(text=dict.edit_title, callback_data="edit_title"),
            InlineKeyboardButton(text=dict.edit_about, callback_data="edit_about")
        ],
        [
            InlineKeyboardButton(text=dict.edit_instr, callback_data="edit_instr"),
            InlineKeyboardButton(text=dict.edit_sdate, callback_data="edit_sdate")
        ],
        [
            InlineKeyboardButton(text=dict.edit_attaches, callback_data="edit_attaches"),
            InlineKeyboardButton(text=dict.edit_ans, callback_data="edit_ans")
        ],
    ]
    btns.append([
            InlineKeyboardButton(text=dict.vis_cur_off, callback_data=f"vis_on") if not visibility else InlineKeyboardButton(text=dict.vis_cur_on, callback_data="vis_off")
        ])
    btns.append([
            InlineKeyboardButton(text=dict.resub_not, callback_data="resub_on") if not resub else InlineKeyboardButton(text=dict.resub_ok, callback_data="resub_off")
        ])
    btns += [
        [
            InlineKeyboardButton(text=dict.delete, callback_data="delete"),
        ],
        [
            InlineKeyboardButton(text=dict.save_changes, callback_data="back"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def details_test(code, folder, exid):
    btns = [
        [
            InlineKeyboardButton(text=dict.folder+folder if folder else dict.folder_not, callback_data="folder")
        ],
        [
            InlineKeyboardButton(text=dict.edit, callback_data=f"edit_{exid}")
            # InlineKeyboardButton(text=dict.share, switch_inline_query=f"ex_{code}")
        ],
        [
            InlineKeyboardButton(text=dict.back, callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

def rm_folders_menu(folders):
    btns = []
    for i, j in folders:
        btns.append([InlineKeyboardButton(text=j, callback_data=f"rmf_{i}")])
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns8 = [
    [
        InlineKeyboardButton(text="Ruxsat olish", callback_data="get_arch"),
    ]
]
arch_inl = InlineKeyboardMarkup(inline_keyboard=btns8)

btns9 = [
    [
        InlineKeyboardButton(text=dict.contin, callback_data="continue"),
    ]
]
continue_inl_to_sett = InlineKeyboardMarkup(inline_keyboard=btns9)

# Statistics menus
btns_stats = [
    [
        InlineKeyboardButton(text=dict.by_user, callback_data="stats_by_user"),
        InlineKeyboardButton(text=dict.by_exam, callback_data="stats_by_exam")
    ],
    [
        InlineKeyboardButton(text=dict.all_submissions, callback_data="stats_all")
    ],
    [
        InlineKeyboardButton(text=dict.export_excel, callback_data="stats_export_select")
    ]
]
stats_menu = InlineKeyboardMarkup(inline_keyboard=btns_stats)

# Export selection menu
btns_export_select = [
    [
        InlineKeyboardButton(text=dict.by_user, callback_data="stats_export_by_user"),
        InlineKeyboardButton(text=dict.by_exam, callback_data="stats_export_by_exam")
    ],
    [
        InlineKeyboardButton(text=dict.all_submissions, callback_data="stats_export_all")
    ],
    [
        InlineKeyboardButton(text=dict.back_to_stats, callback_data="stats_back")
    ]
]
export_select_menu = InlineKeyboardMarkup(inline_keyboard=btns_export_select)


def user_selection_kb(users, page=1, total_pages=1, export_prefix="stats_user_"):
    btns = []
    for user in users:
        display_name = f"{user[2] or 'User'} - {user[1]} - @{user[3] or 'No username'}"
        btns.append([InlineKeyboardButton(text=display_name, callback_data=f"{export_prefix}{user[1]}")])
    if export_prefix.startswith("export_user_"):
        pagination_row = [
            InlineKeyboardButton(text="⏪", callback_data=f"export_users_jump_page_{page-config.USERS_PAGE_JUMP}"),
            InlineKeyboardButton(text="⬅️", callback_data="export_users_prev_page"),
            InlineKeyboardButton(text="➡️", callback_data="export_users_next_page"),
            InlineKeyboardButton(text="⏩", callback_data=f"export_users_jump_page_{page+config.USERS_PAGE_JUMP}")
        ]
    else:
        pagination_row = [
            InlineKeyboardButton(text="⏪", callback_data=f"users_jump_page_{page-config.USERS_PAGE_JUMP}"),
            InlineKeyboardButton(text="⬅️", callback_data="users_prev_page"),
            InlineKeyboardButton(text="➡️", callback_data="users_next_page"),
            InlineKeyboardButton(text="⏩", callback_data=f"users_jump_page_{page+config.USERS_PAGE_JUMP}")
        ]
    btns.append(pagination_row)
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="stats_back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def exam_selection_kb(exams, page=1, total_pages=1, export_prefix="stats_exam_"):
    btns = []
    for exam in exams:
        btns.append([InlineKeyboardButton(text=exam[1], callback_data=f"{export_prefix}{exam[0]}")])
    if export_prefix.startswith("export_exam_"):
        pagination_row = [
            InlineKeyboardButton(text="⏪", callback_data=f"export_exams_jump_page_{page-config.EXAMS_PAGE_JUMP}"),
            InlineKeyboardButton(text="⬅️", callback_data="export_exams_prev_page"),
            InlineKeyboardButton(text="➡️", callback_data="export_exams_next_page"),
            InlineKeyboardButton(text="⏩", callback_data=f"export_exams_jump_page_{page+config.EXAMS_PAGE_JUMP}")
        ]
    else:
        pagination_row = [
            InlineKeyboardButton(text="⏪", callback_data=f"exams_jump_page_{page-config.EXAMS_PAGE_JUMP}"),
            InlineKeyboardButton(text="⬅️", callback_data="exams_prev_page"),
            InlineKeyboardButton(text="➡️", callback_data="exams_next_page"),
            InlineKeyboardButton(text="⏩", callback_data=f"exams_jump_page_{page+config.EXAMS_PAGE_JUMP}")
        ]
    btns.append(pagination_row)
    btns.append([InlineKeyboardButton(text=dict.back, callback_data="stats_back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def submission_details_kb(submissions, page, total_pages):
    """Keyboard for submission details with view buttons and pagination"""
    keyboard = []
    for idx, sub in enumerate(submissions, 1):
        sub_id = sub[0]
        if idx % 2 == 1:
            keyboard.append([InlineKeyboardButton(text=f"👁 #{sub_id}", callback_data=f"view_details_{sub_id}")])
        else:
            keyboard[-1].append(InlineKeyboardButton(text=f"👁 #{sub_id}", callback_data=f"view_details_{sub_id}"))
    
    # Add pagination buttons with big jumps
    pagination_row = [
        InlineKeyboardButton(text=f"⏪", callback_data=f"stats_jump_page_{page-config.SUBMISSIONS_PAGE_JUMP}"),
        InlineKeyboardButton(text="⬅️", callback_data="stats_prev_page"),
        InlineKeyboardButton(text="➡️", callback_data="stats_next_page"),
        InlineKeyboardButton(text=f"⏩", callback_data=f"stats_jump_page_{page+config.SUBMISSIONS_PAGE_JUMP}")
    ]
    
    keyboard.append(pagination_row)
    keyboard.append([InlineKeyboardButton(text=dict.back_to_stats, callback_data="stats_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def submission_detail_back_kb():
    """Back button for submission details view"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=dict.back, callback_data="back_to_submissions")]
    ])