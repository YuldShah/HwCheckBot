from data.dict import check_ans, results, help_txt, archive
from aiogram import types

btns = [
    [
        types.KeyboardButton(text=check_ans)
    ],
    [
        types.KeyboardButton(text=results),
        types.KeyboardButton(text=archive)
    ],
    [
        types.KeyboardButton(text=help_txt)
    ]
]

user_markup = types.ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)