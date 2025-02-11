from aiogram import Router, F, types, html
from data import dict
from aiogram.fsm.context import FSMContext
from loader import db
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from states import arch_states
from keyboards.inline import get_create_folders
from keyboards.regular import main_key

arch = Router()
arch.message.filter(IsAdmin())
arch.callback_query.filter(IsAdminCallback())


@arch.message(F.text == dict.exams)
async def show_folders(message: types.Message, state: FSMContext):
    await message.answer(f"Menu: {html.bold(dict.exams)}", reply_markup=main_key)
    folders = db.fetchall("SELECT * FROM folders")
    print(folders)
    if folders:
        await message.answer(f"Here you can manage the archive of tasks, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    else:
        await message.answer(f"No folders were created yet, you can create a new folder for tests", reply_markup=get_create_folders())
    await state.set_state(arch_states.folders)

@arch.callback_query(CbDataStartsWith("fmng_"), arch_states.folders)
async def show_tests_of_folder(callback: types.CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split("_")[1])
    tests = db.fetchall("SELECT * FROM exams WHERE folder = %s", (folder_id,))
    if tests:
        await callback.message.edit_text(f"Here you can manage the tests of the folder", reply_markup=get_create_folders(tests))
    else:
        await callback.answer("No tests were moved here yet")
        return
    await state.set_state(arch_states.tests)

