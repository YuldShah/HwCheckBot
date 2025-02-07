from aiogram import Router, types, F, html
from data import config, dict
from aiogram.fsm.context import FSMContext
from filters import IsUser, IsUserCallback, CbData, CbDataStartsWith, IsSubscriber

user = Router()

user.message.filter(IsUser(), IsSubscriber())
user.callback_query.filter(IsUserCallback(), IsSubscriber())

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