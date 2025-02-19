from aiogram import Router, types, F, html
from data import config, dict
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards.regular import user_markup
from keyboards.inline import goto_bot, elbek
from .results import results
from filters import IsUser, IsUserCallback, CbData, CbDataStartsWith, IsSubscriber, IsNotArchiveAllowed
from loader import db

user = Router()

user.message.filter(IsUser(), IsSubscriber())
user.callback_query.filter(IsUserCallback(), IsSubscriber())

@user.message(CommandStart())
@user.message(F.text == dict.bosh_menu)
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.text.find("myres")!=-1:
        await results(message, state)
        return
    await message.answer_sticker("CAACAgIAAxkBAAIBt2emDv__wEe3FxrexsQkuXhfqM63AAJAAQACVp29CmzpW0AsSdYlNgQ")
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}! Botga xush kelibsiz!", reply_markup=user_markup)

@user.message(F.text == dict.archive, IsNotArchiveAllowed())
async def archive(message: types.Message):
    cnt = db.fetchone("SELECT COUNT(*) FROM exams LEFT JOIN submissions ON exams.idx = submissions.exid AND submissions.userid = %s::text WHERE submissions.exid IS NULL AND exams.hide = 0", (message.from_user.id,))
    if cnt[0]:
        await message.answer(f"❗️ Sizda {html.bold(cnt[0])} ta qoldirilgan vazifalar mavjud.\n\nAmmo, sizda hozircha qoldirilgan vazifalarni bajarish ruxsati yo'q. Ruxsat olish uchun admin bilan bog'laning.", reply_markup=elbek)
    else:
        await message.answer(f"🎉 Sizda hech qanday qoldirilgan vazifalar yo'q. Albatta, bu yaxshi! 😊")

@user.message(F.text == dict.help_txt)
async def help(message: types.Message):
    await message.answer("Bu yerda botni qanday qilib ishlatishingiz uchun yo'llanmalar bo'ladi. Hozircha hech narsa qo'shilmagan.")

@user.callback_query(CbData("get_perm"))
async def get_perm(callback: types.CallbackQuery):
    # exist = db.fetchone("SELECT idx, allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
    await callback.bot.edit_message_text(text="🎉 Sizga allaqachon ruxsat berilgan! Botdan bemalol foydalanishingiz mumkin!", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
    await callback.answer("🎉 Sizga ruxsat berilgan.")

@user.callback_query(CbData("get_arch"), IsNotArchiveAllowed())
async def get_arch(callback: types.CallbackQuery):
    db.query("UPDATE users SET arch=1 WHERE userid=%s::text", (callback.from_user.id,))
    await callback.bot.edit_message_text(text="🎉 Sizga qoldirilgan vazifalarni bajarish ruxsati berildi! Arxivdan vazifalarni bajarishingiz mumkin!", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
    await callback.answer("🎉 Ruxsat berildi")


@user.callback_query(CbData("main_menu"))
async def main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer_sticker("CAACAgIAAxkBAAIBt2emDv__wEe3FxrexsQkuXhfqM63AAJAAQACVp29CmzpW0AsSdYlNgQ")
    await callback.message.answer(f"👋 Salom, {html.bold(callback.from_user.mention_html())}! Botga xush kelibsiz!", reply_markup=user_markup)