from aiogram import Router, F, types, html
from data import dict
from aiogram.fsm.context import FSMContext
from loader import db
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from states import arch_states
from keyboards.inline import get_create_folders, get_folder_tests
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
        await message.answer(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    else:
        await message.answer(f"No folders were created yet, you can create a new folder for tests, or see the tests from {html.bold(f"{dict.null_folder}")}", reply_markup=get_create_folders())
    await state.set_state(arch_states.folders)

@arch.callback_query(CbDataStartsWith("fmng_"), arch_states.folders)
async def show_tests_of_folder(callback: types.CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split("_")[1])
    tests = db.fetchall("SELECT idx, title FROM exams WHERE folder = %s", (folder_id,))
    if tests:
        await callback.message.edit_text(f"Here you can manage, see the details of the tests in the folder", reply_markup=get_folder_tests(tests))
    else:
        await callback.answer("No tests were moved here yet")
        return
    await state.set_state(arch_states.tests)

@arch.callback_query(CbData("back"), arch_states.tests)
async def back_to_folders(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders())
    await state.set_state(arch_states.folders)

@arch.callback_query(CbDataStartsWith("exman_"), arch_states.tests)
async def manage_test(callback: types.CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split("_")[1])
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (test_id,))
    data = await state.get_data()
    await state.update_data(exam_id=test_id),
                            total=test[4],           # num_questions
                            current=1,
                            # correct=test_info.get("answers", []),
                            # types=test_info.get("types", []),
                            # answers=[None]*test[4])


@arch.callback_query(CbData("add_folders"), arch_states.folders)
async def add_folder(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the name of the folder")
    await state.set_state(arch_states.fol_title)

@arch.message(state=arch_states.fol_title)
async def save_folder(message: types.Message, state: FSMContext):
    folder_name = message.text
    db.execute("INSERT INTO folders (title) VALUES (%s)", (folder_name,))
    await message.answer(f"Folder {html.bold(f"{folder_name}")} created")
    await state.set_state(arch_states.folders)
    await message.answer("Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders())