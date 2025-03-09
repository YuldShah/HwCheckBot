import asyncio
from loader import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def send_notice(chat_id: int, text: str, keyboard: InlineKeyboardMarkup = None):
    await bot.send_message(chat_id, text, reply_markup=keyboard)

btns = [
    [
        InlineKeyboardButton("🤖 Natijalarni botda ko'rish", url="https://t.me/satelbekhc_bot?start=myres")
    ]
]
keyboard = InlineKeyboardMarkup(inline_keyboard=btns)

asyncio.run(send_notice(7345917761, "📊 Natijarlarni tekshirishda botda xatolik ketayotgan ekan. Xatolik to'g'rilandi va natijalaringizni qayta ko'rsangiz bo'ladi.", keyboard))