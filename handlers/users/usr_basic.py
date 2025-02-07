from aiogram import Router, types, F, html
from data import config, dict
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards.regular import user_markup
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

@user.message(F.text == dict.do_todays_hw)
async def do_hw(message: types.Message):
    await message.answer("Bugungi vazifa hali yuklangani yo'q yoki bugunga vazifa yo'q. Agar bu xato deb o'ylasangiz admin bilan bog'laning.")

@user.message(F.text == dict.archive)
async def archive(message: types.Message):
    await message.answer("Bu yerda arxivdagi vazifalar bo'ladi. Hozircha arxivda hech narsa yo'q.")

@user.message(F.text == dict.results)
async def results(message: types.Message):
    await message.answer("Bu yerda sizning natijalaringiz bo'ladi. Hozircha natijalaringiz yo'q.")

@user.message(F.text == dict.help_txt)
async def help(message: types.Message):
    await message.answer("Bu yerda botni qanday qilib ishlatishingiz uchun yo'llanmalar bo'ladi. Hozircha hech narsa qo'shilmagan.")