from aiogram import Router, F, types, html
from data import dict
from aiogram.fsm.context import FSMContext
from loader import db
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from states import arch_states
from keyboards.inline import get_create_folders, get_folder_tests, details_test, edit_test_menu, rm_folders_menu, confirm_inl_key, inl_folders
from keyboards.regular import main_key
import json
from utils.yau import get_text, get_ans_text

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
    data = await state.get_data()
    await callback.message.edit_text("Loading...")
    folder_id = int(callback.data.split("_")[1]) if callback.data.startswith("fmng_") else data.get("folder_id")
    await state.update_data(folder_id=folder_id)
    tests = db.fetchall("SELECT idx, title FROM exams WHERE folder = %s", (folder_id,))
    if tests:
        await callback.message.edit_text(f"Here you can manage, see the details of the tests in the folder", reply_markup=get_folder_tests(tests))
    else:
        await callback.answer("No tests were moved here yet")
        await callback.message.edit_text(f"🚫 Folder doesn't contain any tests. Please, move tests here first")
        await show_folders(callback.message, state)
        return
    await state.set_state(arch_states.tests)

@arch.callback_query(CbData("back"), arch_states.tests)
async def back_to_folders(callback: types.CallbackQuery, state: FSMContext):
    folders = db.fetchall("SELECT * FROM folders")
    await callback.message.edit_text(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    await state.set_state(arch_states.folders)

@arch.callback_query(CbDataStartsWith("exman_"), arch_states.tests)
async def manage_test(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Loading...")
    data = await state.get_data()
    test_id = int(callback.data.split("_")[1]) if callback.data.startswith("exman_") else data.get("exam_id")
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (test_id,))
    print(test)
    
    correct = json.loads(test[5])
    donel = correct.get("answers", [])
    typesl = correct.get("types", [])
    folder = db.fetchone("SELECT title FROM folders WHERE idx = %s", (test[8],))
    if folder:
        folder = folder[0]
    attaches = db.fetchall("SELECT ty, tgfileid, caption FROM attachments WHERE exid = %s", (test_id,))
    await state.update_data(exam_id=test_id, title=test[1], about=test[2], instructions=test[3], numquest=test[4], sdate=test[6], resub=test[7], folder=test[8], hide=test[9], random=test[10], correct=donel, types=typesl, attaches=attaches)
    res = f"{await get_text(state)}\n\n{get_ans_text(donel, typesl)}\n\nYou may edit the test, change its folder or share it:"
    await callback.message.edit_text(res, reply_markup=details_test(test[10], folder, test_id))
    await state.set_state(arch_states.emenu)

@arch.callback_query(F.data == "folder", arch_states.emenu)
async def change_folder(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fod = data.get("folder")
    folders = db.fetchall("SELECT * FROM folders")
    if not folders:
        await callback.answer("No folders found, create one first")
        return
    await state.set_state(arch_states.folder_change)
    await callback.message.edit_text("Please, choose the folder:", reply_markup=inl_folders(folders, fod))
    

@arch.callback_query(F.data.startswith("folder_"), arch_states.folder_change)
async def change_folder_chosen(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fid = callback.data.split("_")[1]
    exid = data.get("exam_id")
    db.query("UPDATE exams SET folder=%s WHERE idx=%s", (fid, exid,))
    await state.update_data(folder_id=fid)
    await callback.answer("Folder changed successfully")
    # await callback.message.edit_text("🗂 Folder changed successfully")
    await manage_test(callback, state)
    # await callback.message.answer(f"Back to menu: {html.bold(dict.exams)}", reply_markup=main_key)
    # folders = db.fetchall("SELECT * FROM folders")
    # print(folders)
    # if folders:
    #     await callback.message.answer(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    # else:
    #     await callback.message.answer(f"No folders were created yet, you can create a new folder for tests, or see the tests from {html.bold(f"{dict.null_folder}")}", reply_markup=get_create_folders())
    # await state.set_state(arch_states.folders)


@arch.callback_query(F.data.startswith("edit_"), arch_states.emenu)
async def edit_test(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exid = callback.data.split("_")[1] if callback.data.startswith("edit_") else data.get("exam_id")
    # exam_id=data.get("exam_id")
    title=data.get("title")
    about=data.get("about")
    instructions=data.get("instructions")
    numquest=data.get("numquest")
    sdate=data.get("sdate")
    resub=data.get("resub")
    folder=data.get("folder")
    hide=data.get("hide")
    correct=data.get("correct")
    typesl=data.get("types")
    attaches=data.get("attaches")
    rand = data.get("random")
    # await state.update_data(exid=exid)
    res = f"{await get_text(state)}\n\n{get_ans_text(correct, typesl)}\n\nYou may edit the test, change its folder or share it:"
    await callback.message.edit_text(res, reply_markup=edit_test_menu(not hide, resub))
    await state.set_state(arch_states.edit)


@arch.callback_query(F.data == "back", arch_states.edit)
async def back_to_test(callback: types.CallbackQuery, state:FSMContext):
    await manage_test(callback, state)
    await callback.answer("Changes saved")
    

@arch.callback_query(F.data == "delete", arch_states.edit)
async def delete_test(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(arch_states.rmtconfirm)
    await callback.message.edit_text("Please, confirm you want to delete the test!", reply_markup=confirm_inl_key)

@arch.callback_query(arch_states.edit, CbDataStartsWith("vis_"))
async def toggle_visibility(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    vis = query.data.split("_")[1]
    exid = data.get("exam_id")
    await query.answer(f"👁 Visibility now - {vis.capitalize()}.")
    if vis == "on":
        db.query("UPDATE exams SET hide = 0 WHERE idx = %s", (exid,))
        # await query.answer("Visibility now on.")
    else:
        db.query("UPDATE exams SET hide = 1 WHERE idx = %s", (exid,))
    # await state.update_data(vis)
    await query.message.edit_reply_markup(reply_markup=edit_test_menu(vis=="on", data.get("resub")))
        # await query.answer("Visibility now off.")
        # vis = "off"
    await state.update_data(hide=vis!="on")

    # await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis=="on", resub, folder))

@arch.callback_query(arch_states.edit, CbDataStartsWith("resub_"))
async def toggle_resubmission(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resub = query.data.split("_")[1]
    exid = data.get("exam_id")
    await query.answer(f"Resubmission now - {resub.capitalize()}.")
    if resub == "on":
        db.query("UPDATE exams SET resub = 1 WHERE idx = %s", (exid,))
        # await query.answer("Visibility now on.")
    else:
        db.query("UPDATE exams SET resub = 0 WHERE idx = %s", (exid,))
        # await query.answer("Visibility now off.")
        # vis = "off"
    await state.update_data(resub=resub=="on")
    await query.message.edit_reply_markup(reply_markup=edit_test_menu(not data.get("hide"), resub=="on"))

    # await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub=="on", folder))


@arch.callback_query(F.data == "confirm", arch_states.rmtconfirm)
async def delete_confirm_test(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Deleting...")
    data = await state.get_data()
    exid = data.get("exam_id")
    db.query("DELETE FROM exams WHERE idx = %s", (exid,))
    # await callback.message.edit_text(f"🗑 Folder {html.bold(data.get("title"))} deleted successfully")
    await callback.answer("Deleted successfully")
    await show_tests_of_folder(callback, state)
    # await callback.message.answer(f"Back to menu: {html.bold(dict.exams)}", reply_markup=main_key)
    # folders = db.fetchall("SELECT * FROM folders")
    # print(folders)
    # if folders:
    #     await callback.message.answer(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    # else:
    #     await callback.message.answer(f"No folders were created yet, you can create a new folder for tests, or see the tests from {html.bold(f"{dict.null_folder}")}", reply_markup=get_create_folders())
    # await state.set_state(arch_states.folders)
    
@arch.callback_query(F.data == "cancel", arch_states.rmtconfirm)
async def cancel_deletion(callback: types.CallbackQuery, state: FSMContext):
    await edit_test(callback, state)
    await callback.answer("Deletion cancelled")


@arch.callback_query(CbData("back"), arch_states.emenu)
async def back_to_tests(callback: types.CallbackQuery, state: FSMContext):
    # test_id = (await state.get_data()).get("exam_id")
    data = await state.get_data()
    folder_id = data.get("folder_id")
    tests = db.fetchall("SELECT idx, title FROM exams WHERE folder = %s", (folder_id,))
    if tests:
        await callback.message.edit_text(f"Here you can manage, see the details of the tests in the folder", reply_markup=get_folder_tests(tests))
    else:
        await callback.answer("Error while fetching tests")
        await state.clear()
        return
    await state.set_state(arch_states.tests)

@arch.callback_query(CbData("add_folder"), arch_states.folders)
async def add_folder(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the name of the folder")
    await state.set_state(arch_states.fol_title)
    await callback.message.delete()

@arch.callback_query(CbData("rm_folder"), arch_states.folders)
async def rm_folder(callback: types.CallbackQuery, state: FSMContext):
    folders = db.fetchall("SELECT * FROM folders")
    await callback.message.edit_text(f"Which folder do you want to delete?", reply_markup=rm_folders_menu(folders))
    await state.set_state(arch_states.rdis)

@arch.callback_query(CbDataStartsWith("rmf_"), arch_states.rdis)
async def rm_folder_confirm(callback: types.CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split("_")[1])
    await state.update_data(folder_id=folder_id)
    await state.set_state(arch_states.rmfconfirm)
    await callback.message.answer("Are you sure you want to delete this folder? It will move all the tests that folder has to null folder", reply_markup=confirm_inl_key)
    await callback.message.delete()
    # await show_folders(callback.message, state)

@arch.callback_query(CbData("back"), arch_states.rdis)
async def back_to_folders(callback: types.CallbackQuery, state: FSMContext):
    folders = db.fetchall("SELECT * FROM folders")
    await callback.message.edit_text(f"Here you can manage the archive of tasks, see the details of tests, change the folders and create a new folder for tests:", reply_markup=get_create_folders(folders))
    await state.set_state(arch_states.folders)

@arch.callback_query(CbData("confirm"), arch_states.rmfconfirm)
async def rm_folder_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    folder_id = data.get("folder_id")
    db.query("DELETE FROM folders WHERE idx = %s", (folder_id,))
    db.query("UPDATE exams SET folder = 0 WHERE folder = %s", (folder_id,))
    await callback.answer("Deleted the folder")
    await show_folders(callback.message, state)
    await callback.message.delete()

arch.callback_query(CbData("cancel"), arch_states.rmfconfirm)
async def cancel_rm_folder(callback: types.CallbackQuery, state: FSMContext):
    await show_folders(callback.message, state)
    await callback.message.delete()

@arch.message(arch_states.fol_title)
async def save_folder(message: types.Message, state: FSMContext):
    folder_name = message.text
    db.query("INSERT INTO folders (title) VALUES (%s)", (folder_name,))
    await message.answer(f"Folder {html.bold(f"{folder_name}")} created")
    await show_folders(message, state)


