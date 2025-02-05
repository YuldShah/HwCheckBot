from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from data import dict

btns1 = [
    [
        KeyboardButton(text=dict.cr_test)
    ],
    [
        KeyboardButton(text=dict.exams),
        KeyboardButton(text=dict.mands)
    ],
    [
        KeyboardButton(text=dict.settings), 
        KeyboardButton(text=dict.stats)
    ]
]

adm_default = ReplyKeyboardMarkup(keyboard=btns1, resize_keyboard=True)

btns2 = [
    [
        KeyboardButton(text=dict.back),
        KeyboardButton(text=dict.skip)
    ]
]
skip_desc = ReplyKeyboardMarkup(keyboard=btns2, resize_keyboard=True)