from data.dict import do_todays_hw, results, help_txt, archive, bosh_menu
from aiogram import types

btns = [
    [
        types.KeyboardButton(text=do_todays_hw)
    ],
    [
        types.KeyboardButton(text=results),
        types.KeyboardButton(text=help_txt)
    ],
    [
        types.KeyboardButton(text=archive)
    ]
]

user_markup = types.ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)

btn1 = [
    [
        types.KeyboardButton(text=bosh_menu, callback_data="main_menu")
    ]
]
usr_main_key = types.ReplyKeyboardMarkup(keyboard=btn1, resize_keyboard=True)