from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, mand
from keyboards.regular import main_key, back_key
from filters import IsUser, IsUserCallback, IsRegistered, IsSubscriber

chhw = Router()
chhw.message.filter(IsUser(), IsSubscriber())
chhw.callback_query.filter(IsUserCallback(), IsSubscriber())

@chhw.message(F.text == dict.do_todays_hw)
async def do_hw(message: types.Message):
    pass