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
    btns = [[InlineKeyboardButton(text=dict.continue_uz, callback_data="continue")]] if confirm else []
    if typesl[current-1] > 0:  # MCQ style
        arow = []
        for i in range(typesl[current-1]):
            arow.append(InlineKeyboardButton(
                text="🟢" if chr(65+i)==answers[current-1] else chr(65+i),
                callback_data=f"mcq_{chr(65+i)}"
            ))
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
    allp = (total + config.MAX_QUESTION_IN_A_PAGE - 1) // config.MAX_QUESTION_IN_A_PAGE
    if allp > 1:
        btns.append([
            InlineKeyboardButton(text="⇐", callback_data="page_prev"),
            InlineKeyboardButton(text=f"Bet: {page}/{allp}", callback_data="page_now"),
            InlineKeyboardButton(text="⇒", callback_data="page_next")
        ])
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns1 = [
    [
        InlineKeyboardButton(text="🖋 Adminga yozish", url=config.ADMIN_URL)
    ]
]

elbek = InlineKeyboardMarkup(inline_keyboard=btns1)

lets_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=dict.start_test, callback_data="start_test")]
])

ans_enter_method_usr = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=dict.all_at_once_uz, callback_data="all"),
     InlineKeyboardButton(text=dict.one_by_one_uz, callback_data="one")]
])

submit_ans_user = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=dict.back_uz, callback_data="back"),
     InlineKeyboardButton(text=dict.send_uz, callback_data="submit")]
])

all_continue_usr = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=dict.continue_uz, callback_data="continue")]
])

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

def get_missing_exams(exams):
    btns = []
    for title, idx in exams:
        btns.append([InlineKeyboardButton(text=title, callback_data=f"mexam_{idx}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns2 = [
    [
        InlineKeyboardButton(text=dict.bosh_menu, callback_data="main_menu")
    ]
]
usr_main_inl_key = InlineKeyboardMarkup(inline_keyboard=btns2)

def get_folders_keyboard(folders, page=1):
    """Create keyboard with folders pagination"""
    btns = []
    
    # Always show null folder (ID 0) at the top if it's in the folders list
    null_folder = next((f for f in folders if f[0] == 0), None)
    if null_folder:
        btns.append([InlineKeyboardButton(text=f"{null_folder[1]}", callback_data=f"folder_0")])
    
    # Sort other folders by ID (newest to oldest)
    other_folders = sorted([f for f in folders if f[0] != 0], key=lambda x: x[0], reverse=True)
    
    # Pagination
    total_pages = max(1, (len(other_folders) + config.MAX_FOLDERS_PER_PAGE - 1) // config.MAX_FOLDERS_PER_PAGE)
    start_idx = (page - 1) * config.MAX_FOLDERS_PER_PAGE
    end_idx = min(start_idx + config.MAX_FOLDERS_PER_PAGE, len(other_folders))
    
    # Add folder buttons for current page
    for folder_id, folder_title in other_folders[start_idx:end_idx]:
        btns.append([InlineKeyboardButton(text=f"{folder_title}", callback_data=f"folder_{folder_id}")])
    
    # Only add navigation buttons if there are multiple pages
    if total_pages > 1:
        nav_row = [
            InlineKeyboardButton(text="⬅️", callback_data="folder_page_prev"),
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="folder_page_now"),
            InlineKeyboardButton(text="➡️", callback_data="folder_page_next")
        ]
        btns.append(nav_row)
    
    return InlineKeyboardMarkup(inline_keyboard=btns)

def get_folder_exams(exams, page=1):
    """Create keyboard with exams pagination for a specific folder"""
    btns = []
    
    # Pagination
    total_pages = max(1, (len(exams) + config.MAX_EXAMS_PER_PAGE - 1) // config.MAX_EXAMS_PER_PAGE if exams else 1)
    start_idx = (page - 1) * config.MAX_EXAMS_PER_PAGE
    end_idx = min(start_idx + config.MAX_EXAMS_PER_PAGE, len(exams) if exams else 0)
    
    # Add exam buttons for current page
    for title, idx in exams[start_idx:end_idx]:
        btns.append([InlineKeyboardButton(text=title, callback_data=f"mexam_{idx}")])
    
    # Only add navigation buttons if there are multiple pages
    if total_pages > 1:
        nav_row = [
            # InlineKeyboardButton(text=dict.earlier, callback_data="mexampage_prev"),
            # InlineKeyboardButton(text=dict.later, callback_data="mexampage_next")
        ]
        if page > 1:
            nav_row.append(InlineKeyboardButton(text=dict.later, callback_data="mexampage_next"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text=dict.earlier, callback_data="mexampage_prev")) 
        btns.append(nav_row)
    
    # Add back button to return to folder selection
    btns.append([InlineKeyboardButton(text=dict.back_uz, callback_data="back_to_folders")])
    
    return InlineKeyboardMarkup(inline_keyboard=btns)
