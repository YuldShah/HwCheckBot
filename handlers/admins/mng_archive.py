from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import get_folder_tests, details_test, edit_test_menu, inl_folders, remove_att, get_create_folders, confirm_inl_key, rm_folders_menu, back_inl_key
from keyboards.regular import main_key, back_key, skip_desc, adm_default, attach_done
from time import sleep
from data import dict, config
from datetime import datetime, timezone, timedelta
from states import arch_states
from aiogram.fsm.context import FSMContext
from utils.yau import get_text, get_ans_text
from .create_test import parse_datetime  # Reuse from create_test.py
import json

arch = Router()
arch.message.filter(IsAdmin())
arch.callback_query.filter(IsAdminCallback())

UTC_OFFSET = timezone(timedelta(hours=5))


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
    
    # Store folder_id and initialize page number
    await state.update_data(folder_id=folder_id, current_test_page=1)
    
    # If folder_id is 0 (All tests), get ALL tests regardless of folder
    # Otherwise, get only tests for the specific folder
    if folder_id == 0:
        tests = db.fetchall("SELECT idx, title FROM exams ORDER BY idx DESC")
    else:
        tests = db.fetchall("SELECT idx, title FROM exams WHERE folder = %s ORDER BY idx DESC", (folder_id,))
    
    if tests:
        # Calculate total pages
        total_pages = max(1, (len(tests) + config.MAX_EXAMS_PER_PAGE - 1) // config.MAX_EXAMS_PER_PAGE)
        await state.update_data(total_test_pages=total_pages)
        
        # Show first page
        folder_name = "All tests" if folder_id == 0 else db.fetchone("SELECT title FROM folders WHERE idx = %s", (folder_id,))[0]
        await callback.message.edit_text(
            f"Here you can manage, see the details of the tests in {folder_name}", 
            reply_markup=get_folder_tests(tests, 1)
        )
    else:
        await callback.answer("No tests were found")
        await callback.message.edit_text(f"🚫 No tests found")
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
    
    # Convert deadline to UTC+5 for admin display
    sdate = test[6]
    if sdate:
        if sdate.tzinfo is None:
            sdate = sdate.replace(tzinfo=timezone.utc)
        sdate = sdate.astimezone(UTC_OFFSET)
    
    correct = json.loads(test[5])
    donel = correct.get("answers", [])
    typesl = correct.get("types", [])
    folder = db.fetchone("SELECT title FROM folders WHERE idx = %s", (test[8],))
    if folder:
        folder = folder[0]
    attaches = db.fetchall("SELECT ty, tgfileid, caption FROM attachments WHERE exid = %s", (test_id,))
    
    # Store UTC+5 time in state for display
    await state.update_data(
        exam_id=test_id, 
        title=test[1], 
        about=test[2], 
        instructions=test[3], 
        numquest=test[4], 
        sdate=sdate,  # Now in UTC+5 for display
        resub=test[7], 
        folder=test[8], 
        hide=test[9], 
        random=test[10], 
        correct=donel, 
        types=typesl, 
        attaches=attaches
    )
    
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

@arch.callback_query(F.data == "back", arch_states.folder_change)
async def back_to_test(callback: types.CallbackQuery, state: FSMContext):
    await manage_test(callback, state)

async def refresh_edit_menu(message: types.Message, state: FSMContext, oddiy: bool = False):
    data = await state.get_data()
    exam_id = data["exam_id"]
    exam = db.fetchone("SELECT * FROM exams WHERE idx = %s", (exam_id,))
    
    # Handle dates for display
    sdate = exam[6]
    if sdate:
        # Convert to UTC+5 for display purposes
        if sdate.tzinfo is None:
            sdate = sdate.replace(tzinfo=timezone.utc)
        sdate = sdate.astimezone(UTC_OFFSET)
    
    correct = json.loads(exam[5])
    donel = correct.get("answers", [])
    typesl = correct.get("types", [])
    folder = db.fetchone("SELECT title FROM folders WHERE idx = %s", (exam[8],))
    if folder:
        folder = folder[0]
    attaches = db.fetchall("SELECT ty, tgfileid, caption FROM attachments WHERE exid = %s", (exam_id,))
    
    # Update state with proper timezone-aware datetime
    await state.update_data(
        exam_id=exam_id,
        title=exam[1],
        about=exam[2],
        instructions=exam[3],
        numquest=exam[4],
        sdate=sdate,  # This is now in UTC+5 for display
        resub=exam[7],
        folder=exam[8],
        hide=exam[9],
        random=exam[10],
        correct=donel,
        types=typesl,
        attaches=attaches
    )
    
    res = f"{await get_text(state)}\n\n{get_ans_text(donel, typesl)}\n\nYou may edit the test, change its folder or share it:"
    if oddiy:
        await message.answer(res, reply_markup=edit_test_menu(not exam[9], exam[7]))
    else:
        await message.edit_text(res, reply_markup=edit_test_menu(not exam[9], exam[7]))
    await state.set_state(arch_states.edit)

@arch.callback_query(F.data.startswith("edit_"), arch_states.emenu)
async def edit_test(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exid = callback.data.split("_")[1] if callback.data.startswith("edit_") else data.get("exam_id")
    
    # Get the data
    title=data.get("title")
    about=data.get("about")
    instructions=data.get("instructions")
    numquest=data.get("numquest")
    sdate=data.get("sdate")  # This should already be in UTC+5 from manage_test
    resub=data.get("resub")
    folder=data.get("folder")
    hide=data.get("hide")
    correct=data.get("correct")
    typesl=data.get("types")
    attaches=data.get("attaches")
    rand=data.get("random")
    
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

@arch.callback_query(CbData("cancel"), arch_states.rmfconfirm)
async def cancel_rm_folder(callback: types.CallbackQuery, state: FSMContext):
    await show_folders(callback.message, state)
    await callback.message.delete()

@arch.message(arch_states.fol_title)
async def save_folder(message: types.Message, state: FSMContext):
    folder_name = message.text
    db.query("INSERT INTO folders (title) VALUES (%s)", (folder_name,))
    await message.answer(f"Folder {html.bold(f"{folder_name}")} created")
    await show_folders(message, state)


@arch.callback_query(F.data == "edit_title", arch_states.edit)
async def start_edit_title(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    await callback.message.edit_text(f"{res}\n\nPlease send the new title:", reply_markup=back_inl_key)
    await state.set_state(arch_states.title)

@arch.callback_query(CbData("back"), arch_states.title)
async def back_from_title_cb(callback: types.CallbackQuery, state: FSMContext):
    # await callback.message.delete()
    await refresh_edit_menu(callback.message, state)
    await callback.answer()

@arch.message(arch_states.title)
async def save_new_title(message: types.Message, state: FSMContext):
    new_title = message.text
    data = await state.get_data()
    exam_id = data["exam_id"]
    db.query("UPDATE exams SET title = %s WHERE idx = %s", (new_title, exam_id))
    await state.update_data(title=new_title)
    await message.delete()
    await refresh_edit_menu(message, state, oddiy=True)


@arch.callback_query(F.data == "edit_about", arch_states.edit)
async def start_edit_description(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    await callback.message.edit_text(f"{res}\n\nPlease send the new description (or 'skip' to clear):", reply_markup=back_inl_key)
    await state.set_state(arch_states.about)

@arch.callback_query(CbData("back"), arch_states.about)
async def back_from_about_cb(callback: types.CallbackQuery, state: FSMContext):
    # await callback.message.delete()
    await refresh_edit_menu(callback.message, state)
    await callback.answer()

@arch.message(arch_states.about)
async def save_new_description(message: types.Message, state: FSMContext):
    new_description = None if message.text.lower() == "skip" else message.text
    data = await state.get_data()
    exam_id = data["exam_id"]
    db.query("UPDATE exams SET about = %s WHERE idx = %s", (new_description, exam_id))
    await state.update_data(about=new_description)
    await message.delete()
    await refresh_edit_menu(message, state, oddiy=True)


@arch.callback_query(F.data == "edit_instr", arch_states.edit)
async def start_edit_instructions(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    await callback.message.edit_text(f"{res}\n\nPlease send the new instructions:", reply_markup=back_inl_key)
    await state.set_state(arch_states.instruc)

@arch.callback_query(CbData("back"), arch_states.instruc)
async def back_from_instructions_cb(callback: types.CallbackQuery, state: FSMContext):
    # await callback.message.delete()
    await refresh_edit_menu(callback.message, state)
    await callback.answer()

@arch.message(arch_states.instruc)
async def save_new_instructions(message: types.Message, state: FSMContext):
    new_instructions = message.text
    data = await state.get_data()
    exam_id = data["exam_id"]
    db.query("UPDATE exams SET instructions = %s WHERE idx = %s", (new_instructions, exam_id))
    await state.update_data(instructions=new_instructions)
    await message.delete()
    await refresh_edit_menu(message, state, oddiy=True)

@arch.callback_query(F.data == "edit_ans", arch_states.edit)
async def start_edit_answers(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    # Fixed HTML parsing error by not using angle brackets
    await callback.message.edit_text(
        f"{res}\n\nSend the question number, answer, and number of options in format (seperate the parts with |): {html.code('question answer options')}.\n"
        f"Example: {html.code('5 | A | 4')} for question 5, answer A, 4 options.", 
        reply_markup=back_inl_key
    )
    await state.set_state(arch_states.edans)

@arch.callback_query(CbData("back"), arch_states.edans)
async def back_from_answers_cb(callback: types.CallbackQuery, state: FSMContext):
    # await callback.message.delete()
    await refresh_edit_menu(callback.message, state)
    await callback.answer()

@arch.message(arch_states.edans)
async def save_new_answer(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split("|")
        if len(parts) != 3:
            raise ValueError(f"Invalid format. Use: {html.code('&lt;question&gt; &lt;answer&gt; &lt;options&gt;')}")
        q_num = int(parts[0]) - 1  # Convert to 0-based index
        answer = parts[1]
        options = int(parts[2])
        if options == 1:
            raise ValueError(f"Can't have {html.bold("\"multiple\"")} choice question with 1 choice")
        if options < 0 or options > 6:
            raise ValueError("Options must be 0 (open-ended) or 2-6.")
        
        data = await state.get_data()
        exam_id = data["exam_id"]
        correct_json = json.loads(db.fetchone("SELECT correct FROM exams WHERE idx = %s", (exam_id,))[0])
        
        if q_num < 0 or q_num >= len(correct_json["answers"]):
            raise ValueError("Question number out of range.")
        
        correct_json["answers"][q_num] = answer
        correct_json["types"][q_num] = options
        db.query("UPDATE exams SET correct = %s WHERE idx = %s", (json.dumps(correct_json), exam_id))
        
        # Update state data
        data["correct"] = correct_json["answers"]
        data["types"] = correct_json["types"]
        await state.update_data(correct=correct_json["answers"], types=correct_json["types"])
        
        await message.delete()
        await refresh_edit_menu(message, state, oddiy=True)
    except ValueError as e:
        msg = await message.answer(f"Error: {str(e)} Please try again.")
        await message.delete()
        sleep(2)
        await msg.delete()

async def display_attachments(message: types.Message, state: FSMContext):
    data = await state.get_data()
    attaches = data.get("attaches", [])
    for idx, (att_type, file_id, caption) in enumerate(attaches):
        if att_type == "document":
            await message.answer_document(document=file_id, caption=caption, reply_markup=remove_att(idx))
        elif att_type == "photo":
            await message.answer_photo(photo=file_id, caption=caption, reply_markup=remove_att(idx))

@arch.callback_query(F.data == "edit_attaches", arch_states.edit)
async def start_edit_attachments(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    await callback.message.edit_text(f"{res}\n\nSend new attachments or remove existing ones. Press Done when finished.")
    await display_attachments(callback.message, state)
    await callback.message.answer("Attachment management:", reply_markup=attach_done)
    await state.set_state(arch_states.attaches)

# THIS HANDLER MUST BE REGISTERED FIRST - order matters
@arch.message(F.text == dict.done, arch_states.attaches)
async def done_attachments(message: types.Message, state: FSMContext):
    await message.answer("Successfully saved the attachments", reply_markup=main_key)
    await message.delete()
    await refresh_edit_menu(message, state, oddiy=True)

# This handler must come AFTER the dict.done handler
@arch.message(arch_states.attaches)
async def add_attachment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    exam_id = data.get("exam_id")
    attaches = data.get("attaches", [])
    
    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        ty = "photo"
    elif message.document:
        file_id = message.document.file_id
        caption = message.caption or ""
        ty = "document"
    else:
        await message.answer("Please send a photo or document.", reply_markup=attach_done)
        return
    
    # Add to database
    db.query("INSERT INTO attachments (exid, ty, tgfileid, caption) VALUES (%s, %s, %s, %s)", 
             (exam_id, ty, file_id, caption))
    
    # Update state data
    attaches.append((ty, file_id, caption))
    await state.update_data(attaches=attaches)
    
    await message.reply(f"Attachment added successfully.", reply_markup=attach_done)

@arch.callback_query(CbDataStartsWith("rma_"), arch_states.attaches)
async def remove_attachment(query: types.CallbackQuery, state: FSMContext):
    idx = int(query.data.split("_")[1])
    data = await state.get_data()
    exam_id = data.get("exam_id")
    attaches = data.get("attaches", [])
    
    if 0 <= idx < len(attaches):
        # Remove from database - need to get the actual attachment ID
        attachment = db.fetchone("SELECT idx FROM attachments WHERE exid = %s AND tgfileid = %s", 
                                (exam_id, attaches[idx][1]))
        if attachment:
            db.query("DELETE FROM attachments WHERE idx = %s", (attachment[0],))
        
        # Remove from state
        attaches.pop(idx)
        await state.update_data(attaches=attaches)
        
        await query.answer("Attachment removed.")
        await query.message.delete()
    else:
        await query.answer("Attachment not found.")

@arch.callback_query(F.data == "edit_sdate", arch_states.edit)
async def start_edit_deadline(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    res = f"{await get_text(state)}\n\n{get_ans_text(data.get('correct', []), data.get('types', []))}"
    await callback.message.edit_text(f"{res}\n\nPlease send the new deadline (e.g., HH:MM DD MM YYYY):", reply_markup=back_inl_key)
    await state.set_state(arch_states.sdate)

@arch.callback_query(CbData("back"), arch_states.sdate)
async def back_from_deadline_cb(callback: types.CallbackQuery, state: FSMContext):
    # await callback.message.delete()
    await refresh_edit_menu(callback.message, state)
    await callback.answer()

@arch.message(arch_states.sdate)
async def save_new_deadline(message: types.Message, state: FSMContext):
    try:
        # Parse the datetime from user input (assuming it's in UTC+5 from admin perspective)
        new_deadline = parse_datetime(message.text)
        
        # Always treat admin input as UTC+5, then convert to UTC for storage
        if new_deadline.tzinfo is None:
            # If naive datetime, explicitly set it as UTC+5
            new_deadline = new_deadline.replace(tzinfo=UTC_OFFSET)
            # Then convert to UTC for storage
            new_deadline = new_deadline.astimezone(timezone.utc)
        
        data = await state.get_data()
        exam_id = data["exam_id"]
        
        # Store in database as UTC
        db.query("UPDATE exams SET sdate = %s WHERE idx = %s", (new_deadline, exam_id))
        
        # For display purposes in state, convert back to UTC+5
        display_deadline = new_deadline.astimezone(UTC_OFFSET)
        await state.update_data(sdate=display_deadline)
        
        await message.delete()
        await refresh_edit_menu(message, state, oddiy=True)
    except ValueError:
        msg = await message.answer("Invalid format. Please use HH:MM DD MM YYYY.")
        await message.delete()
        sleep(2)
        await msg.delete()

@arch.callback_query(CbDataStartsWith("tests_page_"), arch_states.tests)
async def navigate_test_pages(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[2]  # prev, next, or now
    data = await state.get_data()
    current_page = data.get("current_test_page", 1)
    folder_id = data.get("folder_id")
    total_pages = data.get("total_test_pages", 1)
    
    # Adjust page based on action
    if action == "prev":
        if current_page > 1:
            current_page -= 1
        else:
            await callback.answer("Already on the first page")
            return
    elif action == "next":
        if current_page < total_pages:
            current_page += 1
        else:
            await callback.answer("Already on the last page")
            return
    else:  # now - showing current page info
        await callback.answer(f"Page {current_page} of {total_pages}")
        return
    
    # Update state with new page
    await state.update_data(current_test_page=current_page)
    
    # Get tests for this folder again
    if folder_id == 0:
        tests = db.fetchall("SELECT idx, title FROM exams ORDER BY idx DESC")
    else:
        tests = db.fetchall("SELECT idx, title FROM exams WHERE folder = %s ORDER BY idx DESC", (folder_id,))
    
    # Update the message with the correct page
    folder_name = "All tests" if folder_id == 0 else db.fetchone("SELECT title FROM folders WHERE idx = %s", (folder_id,))[0]
    await callback.message.edit_text(
        f"Here you can manage, see the details of the tests in {folder_name}", 
        reply_markup=get_folder_tests(tests, current_page)
    )