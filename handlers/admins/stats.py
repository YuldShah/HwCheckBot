from aiogram import types, Router, F, html
from data import dict
from keyboards.regular import main_key
# from keyboards.inline import refresh_key
from states import statsstates
from aiogram.fsm.context import FSMContext
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith

stater = Router()
stater.message.filter(IsAdmin())
stater.callback_query.filter(IsAdminCallback())

@stater.message(F.text == dict.stats)
async def show_stats(message: types.Message, state: FSMContext):
    await message.answer(f"Menu {html.bold(f"{dict.stats}")}", reply_markup=main_key)
    response = "Here you can see the statistics of the bot, the number of users, the number of submissions received and etc."
    await message.answer(response)
    await state.set_state(statsstates.stmenu)
