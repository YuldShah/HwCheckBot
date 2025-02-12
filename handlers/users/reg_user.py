# can be used later to add phone numbers of the users later

from aiogram import types, Router, html
from filters import IsNotRegistered, IsUser, IsNotSubscriber, IsUserCallback, CbData, CbDataStartsWith, IsSubscriber
from loader import db
from aiogram.filters import or_f
from keyboards.regular import user_markup
from keyboards.inline import elbek, goto_bot
from data import config
from utils.yau import checksub
# from keyboards.keyboard import user_markup

reger = Router()

reger.message.filter(IsUser(), IsNotRegistered())
reger.callback_query.filter(IsUserCallback(), IsNotRegistered())

@reger.message(IsNotSubscriber())
async def process_command(message: types.Message) -> None:
    db.query("INSERT INTO users (userid, fullname, username) VALUES (%s, %s, %s)", (message.from_user.id, message.from_user.full_name, message.from_user.username))
    # response = f"👋 Heyy, <b>{message.from_user.first_name}</b>."
    # channels = db.fetchone("SELECT * FROM channel")
    # if not channels:
    msg = await message.answer("Yuklanmoqda...", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}!\n\n❌ Siz hali botdan foydalanish uchun ruxsat olganingiz yo'q yoki kursga ro'yxatdan o'tganlar orasidan topilmadingiz.\n\n✍️Iltimos, adminga yozib ro'yxatdan o'ting.", reply_markup=elbek)
    await msg.delete()

@reger.message(IsSubscriber())
async def start(message: types.Message):
    db.query("INSERT INTO users (userid, fullname, username, allowed) VALUES (%s, %s, %s, 1)", (message.from_user.id, message.from_user.full_name, message.from_user.username))
    # await state.clear()
    await message.answer_sticker("CAACAgIAAxkBAAIBt2emDv__wEe3FxrexsQkuXhfqM63AAJAAQACVp29CmzpW0AsSdYlNgQ", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}! Botga xush kelibsiz!", reply_markup=user_markup)

@reger.callback_query(CbData("get_perm"), IsNotSubscriber())
async def get_perm(callback: types.CallbackQuery):

    exist = db.fetchone("SELECT idx, allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
    if not exist:
        db.query("INSERT INTO users (userid, fullname, username, allowed) VALUES (%s, %s, %s, 1)", (callback.from_user.id, callback.from_user.full_name, callback.from_user.username))
    else:
        if exist[1] == 1:
            await callback.bot.edit_message_text(text="🎉 Sizga allaqachon ruxsat berilgan! Botdan bemalol foydalanishingiz mumkin!", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
            await callback.answer("🎉 Sizga ruxsat berilgan.")
            return
        db.query("UPDATE users SET allowed=1 WHERE userid=%s::text", (callback.from_user.id,))
    try:
        await callback.bot.send_message(callback.from_user.id, "🎉 Tabriklaymiz, sizga botdan foydalanish ruxsati berildi. /start buyrug'ini jo'nating.", reply_markup=user_markup)
    except:
        await callback.answer("🎉 Ruxsat berildi. Sizga xabar jo'natib bo'lmadi.")
    await callback.bot.edit_message_text(text="🎉 Tabriklaymiz, sizga botdan foydalanish ruxsati berildi. Endi bemalol botga kirib ishlatishingiz mumkin.", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
    await callback.answer("🎉 Ruxsat berildi")