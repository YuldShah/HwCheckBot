from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data import dict

btns = [
    [
        InlineKeyboardButton(text=dict.main_menu, callback_data="main_menu")
    ]
]
main_menu_in = InlineKeyboardMarkup(inline_keyboard=btns)

btns1 = [
    [
        InlineKeyboardButton(text=dict.back, callback_data="back"),
    ]
]
back_inl_key = InlineKeyboardMarkup(inline_keyboard=btns1)