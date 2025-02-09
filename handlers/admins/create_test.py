from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
# from keyboards.inline import test_key
from keyboards.regular import main_key, back_key, skip_desc
from data import dict
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
    await state.update_data(duration=None)
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
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.instructions, F.text == dict.back)
async def back_to_about(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.instructions)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.number)
async def get_number(message: types.Message, state: FSMContext):
    await state.update_data(numquest=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the start date in one of the following formats:\n{html.code(f"DD MM YYYY HH MM\nHH MM")} - for today", reply_markup=back_key)
    await state.set_state(creates.sdate)
