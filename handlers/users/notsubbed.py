# can be used later to add phone numbers of the users later

from aiogram import types, Router, html
from filters import IsNotRegistered, IsUser, IsNotSubscriber, IsUserCallback, CbData, CbDataStartsWith, IsSubscriber, IsRegistered
from loader import db
from aiogram.filters import or_f
from keyboards.regular import user_markup
from keyboards.inline import elbek, goto_bot
from data import config
from utils.yau import checksub
# from keyboards.keyboard import user_markup

nosub = Router()

nosub.message.filter(IsUser(), IsNotSubscriber(), IsRegistered())
nosub.callback_query.filter(IsUserCallback(), IsNotSubscriber(), IsRegistered())

@nosub.message()
async def process_command(message: types.Message) -> None:
    msg = await message.answer("Yuklanmoqda...", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}!\n\n❌ Siz hali botdan foydalanish uchun ruxsat olganingiz yo'q yoki kursga ro'yxatdan o'tganlar orasidan topilmadingiz.\n\n✍️Iltimos, adminga yozib ro'yxatdan o'ting.", reply_markup=elbek)
    await msg.delete()

@nosub.callback_query(CbData("get_perm"))
async def get_perm(callback: types.CallbackQuery):
    db.query("UPDATE users SET allowed=1 WHERE userid=%s::text", (callback.from_user.id,))
    try:
        await callback.bot.send_message(callback.from_user.id, "🎉 Tabriklaymiz, sizga botdan foydalanish ruxsati berildi. /start buyrug'ini jo'nating.", reply_markup=user_markup)
    except:
        await callback.answer("🎉 Ruxsat berildi. Sizga xabar jo'natib bo'lmadi.")
    await callback.bot.edit_message_text(text="🎉 Tabriklaymiz, sizga botdan foydalanish ruxsati berildi. Endi bemalol botga kirib ishlatishingiz mumkin.", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
    await callback.answer("🎉 Ruxsat berildi")

@nosub.callback_query()
async def nah_uh(callback: types.CallbackQuery):
    msg = await callback.message.answer("Yuklanmoqda...", reply_markup=types.ReplyKeyboardRemove())
    await callback.answer("Botdan foydalana olmaysiz!")
    await callback.message.answer(f"👋 Salom, {html.bold(callback.from_user.mention_html())}!\n\n❌ Siz hali botdan foydalanish uchun ruxsat olganingiz yo'q yoki kursga ro'yxatdan o'tganlar orasidan topilmadingiz.\n\n✍️Iltimos, adminga yozib ro'yxatdan o'ting.", reply_markup=elbek)
    await msg.delete()