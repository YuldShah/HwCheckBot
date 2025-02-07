from data.dict import do_todays_hw, results, help_txt, archive
from aiogram import types

btns = [
    [
        types.KeyboardButton(text=do_todays_hw)
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