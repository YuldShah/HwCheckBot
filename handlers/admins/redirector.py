from aiogram import Router, types, F, html
from data import config
from aiogram.fsm.context import FSMContext
from states import sets
from keyboards.regular import main_key
from keyboards.inline import set_menu
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith


redirector = Router()
redirector.message.filter(IsAdmin())
redirector.callback_query.filter(IsAdminCallback())

@redirector.message(F.text == dict.settings)
async def sett(message: types.Message, state: FSMContext):
    await state.set_state(sets.smenu)
    await message.answer(f"Menu: <b>{dict.settings}</b>", reply_markup=main_key)
    response = "Here you can change some configuration settings and manage permission giving chat"
    await message.answer(response, reply_markup=set_menu)