from aiogram import Router, types, F, html
from data import config, dict
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards.regular import user_markup
from keyboards.inline import goto_bot
from filters import IsUser, IsUserCallback, CbData, CbDataStartsWith, IsSubscriber

user = Router()

user.message.filter(IsUser(), IsSubscriber())
user.callback_query.filter(IsUserCallback(), IsSubscriber())

@user.message(CommandStart())
@user.message(F.text == dict.main_menu)
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer_sticker("CAACAgIAAxkBAAIBt2emDv__wEe3FxrexsQkuXhfqM63AAJAAQACVp29CmzpW0AsSdYlNgQ")
    await message.answer(f"👋 Salom, {html.bold(message.from_user.mention_html())}! Botga xush kelibsiz!", reply_markup=user_markup)

@user.message(F.text == dict.archive)
async def archive(message: types.Message):
    await message.answer("Bu yerda arxivdagi vazifalar bo'ladi. Hozircha arxivda hech narsa yo'q.")

@user.message(F.text == dict.results)
async def results(message: types.Message):
    await message.answer("Bu yerda sizning natijalaringiz bo'ladi. Hozircha natijalaringiz yo'q.")

@user.message(F.text == dict.help_txt)
async def help(message: types.Message):
    await message.answer("Bu yerda botni qanday qilib ishlatishingiz uchun yo'llanmalar bo'ladi. Hozircha hech narsa qo'shilmagan.")


@user.callback_query(CbData("get_perm"))
async def get_perm(callback: types.CallbackQuery):
    # exist = db.fetchone("SELECT idx, allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
    await callback.bot.edit_message_text(text="🎉 Sizga allaqachon ruxsat berilgan! Botdan bemalol foydalanishingiz mumkin!", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))
    await callback.answer("🎉 Sizga ruxsat berilgan.")