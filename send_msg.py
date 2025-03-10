import asyncio
from loader import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def send_notice(chat_id: int, text: str, keyboard: InlineKeyboardMarkup = None):
    await bot.send_message(chat_id, text, reply_markup=keyboard)

btns = [
    [
        InlineKeyboardButton(text="🤖 Natijalarni botda ko'rish", url="https://t.me/satelbekhc_bot?start=myres")
    ]
]
keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
chat_id = input("Enter chat id: ") # 1002264412537 - group, -1002258255154 - channel
msg = input("Enter message: ")

loop = asyncio.get_event_loop()
loop.run_until_complete(send_notice(int(chat_id), msg, keyboard))
loop.close()