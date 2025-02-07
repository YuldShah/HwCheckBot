from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat
from data.dict import check_subs
from data import config

def mand_chans(channels) -> InlineKeyboardMarkup:
    btns = []
    for name, idx, url in channels:
        btns.append([InlineKeyboardButton(text=name, url=url)])
    btns.append([InlineKeyboardButton(text=check_subs, callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

btns1 = [
    [
        InlineKeyboardButton(text="🖋 Adminga yozish", url=config.ADMIN_URL)
    ]
]

elbek = InlineKeyboardMarkup(inline_keyboard=btns1)