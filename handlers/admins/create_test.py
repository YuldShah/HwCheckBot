from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import today, ans_enter_meth, obom
from keyboards.regular import main_key, back_key, skip_desc
from data import dict
from datetime import datetime, timedelta
from states import creates
from aiogram.fsm.context import FSMContext
from utils.yau import get_text

test = Router()

test.message.filter(IsAdmin())
test.callback_query.filter(IsAdminCallback())


@test.message(F.text == dict.cr_test)
async def create_test(message: types.Message, state: FSMContext):
    await message.answer(f"Please, send the title.", reply_markup=main_key)
    await state.set_state(creates.title)
    await state.update_data(title=None)
    await state.update_data(about=None)
    await state.update_data(instructions=None)
    await state.update_data(numquest=None)
    await state.update_data(sdate=None)
    # await state.update_data(duration=None)
    # title=data.get("title")
    # about=data.get("about")
    # instructions=data.get("instructions")
    # numquest=data.get("numquest")
    # sdate=data.get("sdate")
    # duration=data.get("duration")

@test.message(creates.title)
async def get_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.about, F.text == dict.skip)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=None)
    await message.answer(f"{await get_text(state)}\nPlease, send the instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.about, F.text==dict.back)
async def back_to_title(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the title.", reply_markup=main_key)
    await state.set_state(creates.title)

@test.message(creates.about)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.instructions, F.text == dict.skip)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=None)
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.instructions, F.text == dict.back)
async def back_to_about(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.instructions)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.number, F.text == dict.back)
async def back_to_instructions(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.number)
async def get_number(message: types.Message, state: FSMContext):
    await state.update_data(numquest=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the date in the following format:\n{html.code(f"DD MM YYYY")}", reply_markup=today)
    await state.set_state(creates.sdate)

@test.message(creates.sdate, F.text == dict.back)
async def back_to_number(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.sdate)
async def get_sdate(message: types.Message, state: FSMContext):

    await state.update_data(sdate=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers:", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.callback_query(CbData("today"), creates.sdate)
async def set_date_today(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(sdate=(datetime.now(datetime.timezone.utc) + timedelta(hours=5)).strftime("%d %m %Y"))
    await query.message.edit_text(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers:", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.callback_query(CbData("back"), creates.way)
async def back_to_date(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(f"{await get_text(state)}\nPlease, send the date in the following format or press the following to set it for today:\n{html.code(f'DD MM YYYY')}", reply_markup=today)
    await state.set_state(creates.sdate)

@test.callback_query(CbData("all"), creates.way)
async def set_way_all(query: types.CallbackQuery, state: FSMContext):
    # await state.update_data(duration=None)
    await state.update_data(ans=None)
    await query.message.edit_text(f"{await get_text(state)}\nPlease, send the answers in the following format:\n{html.code('Answer1\nAnswer2\nAnswer3,AgainAnswer3')}")
    await state.set_state(creates.ans)

@test.callback_query(CbData("one"), creates.way)
async def set_way_one(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(ans=None)
    await state.update_data(curq=1)
    await state.update_data(type=1)
    numq = int(await state.get_data()).get("numquest")
    await query.message.edit_text(f"{await get_text(state)}\nPlease, choose the right answer for question {html.bold("#1")}:", reply_markup=obom(1, numq, [], 1))
    await state.set_state(creates.ans)