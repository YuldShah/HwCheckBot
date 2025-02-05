from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from data import dict

btns1 = [
    [
        KeyboardButton(text=dict.back)
    ]
]

back_key = ReplyKeyboardMarkup(keyboard=btns1, resize_keyboard=True)

btns2 = [
    [
        KeyboardButton(text=dict.main_menu)
    ]
]

main_key = ReplyKeyboardMarkup(keyboard=btns2, resize_keyboard=True)