# can be used later to add phone numbers of the users later

from aiogram import types, Router, html
from filters import IsNotRegistered, IsUser
from loader import db
from keyboards.inline import mand_chans, elbek
# from utils.yau import notsubbed
# from keyboards.keyboard import user_markup

reger = Router()

reger.message.filter(IsNotRegistered(), IsUser())

@reger.message()
async def process_command(message: types.Message) -> None:
    db.query("INSERT INTO users (userid, fullname, username) VALUES (%s, %s, %s)", (message.from_user.id, message.from_user.full_name, message.from_user.username))
    # response = f"👋 Heyy, <b>{message.from_user.first_name}</b>."
    # channels = await notsubbed(message.from_user.id)
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}. Siz kursga ro'yxatdan o'tganlar orasidan topilmadingiz iltimos adminga yozib ro'yxatdan o'ting.", reply_markup=elbek)