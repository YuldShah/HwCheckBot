# can be used later to add phone numbers of the users later

from aiogram import types, Router, html
from filters import IsNotRegistered, IsUser, IsNotSubscriber, IsUserCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import elbek, goto_bot
from data import config
# from utils.yau import notsubbed
# from keyboards.keyboard import user_markup

reger = Router()

reger.message.filter(IsUser())
reger.callback_query.filter(IsNotRegistered() | IsNotSubscriber(), IsUserCallback())

@reger.message()
async def process_command(message: types.Message) -> None:
    db.query("INSERT INTO users (userid, fullname, username) VALUES (%s, %s, %s)", (message.from_user.id, message.from_user.full_name, message.from_user.username))
    # response = f"👋 Heyy, <b>{message.from_user.first_name}</b>."
    # channels = await notsubbed(message.from_user.id)
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}. Siz kursga ro'yxatdan o'tganlar orasidan topilmadingiz iltimos adminga yozib ro'yxatdan o'ting.", reply_markup=elbek)

@reger.callback_query(CbData("get_perm"))
async def get_perm(callback: types.CallbackQuery):
    exist = db.fetchone("SELECT idx FROM users WHERE userid=%s::text", (callback.from_user.id,))
    if not exist:
        db.query("INSERT INTO users (userid, fullname, username, allowed) VALUES (%s, %s, %s, 1)", (callback.from_user.id, callback.from_user.full_name, callback.from_user.username))
    else:
        db.query("UPDATE users SET allowed=1 WHERE userid=%s::text", (callback.from_user.id,))
    await callback.bot.edit_message_text(text="Ruxsat berildi. Endi bemalol botga kirib ishlatishingiz mumkin.", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))