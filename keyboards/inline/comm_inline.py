from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data import dict

btns = [
    [
        InlineKeyboardButton(text=dict.main_menu, callback_data="main_menu")
    ]
]
main_menu_in = InlineKeyboardMarkup(inline_keyboard=btns)
