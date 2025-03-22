from aiogram import Router, F, html, types
from filters import IsUser, IsSubscriber, IsUserCallback, IsSubscriberCallback, IsArchiveAllowed, IsArchiveAllowedCallback
from data import dict, config
from loader import db
from time import sleep
from aiogram.fsm.context import FSMContext
from keyboards.regular import usr_main_key
from keyboards.inline import (lets_start, ans_enter_method_usr, goto_bot, submit_ans_user, 
                             all_continue_usr, get_missing_exams, get_answering_keys, share_sub_usr, 
                             get_folders_keyboard, get_folder_exams)
from datetime import datetime, timezone, timedelta
from states import missing_hw_states
from utils.yau import get_user_text, get_user_ans_text, get_correct_text, gen_code
from aiogram.exceptions import TelegramBadRequest

usrarch = Router()
usrarch.message.filter(IsUser(), IsSubscriber())
usrarch.callback_query.filter(IsUserCallback(), IsSubscriberCallback())

@usrarch.message(F.text == dict.archive)
async def show_archive(message: types.Message, state: FSMContext):
    await message.answer(f"{html.bold(dict.archive)} menyusi", reply_markup=usr_main_key)
    msg = await message.answer("Yuklanmoqda...")
    
    # Get all folders with tests
    folders_with_tests = []
    
    # Always include uncategorized folder (ID 0)
    uncategorized_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = 0 AND hide = 0")
    if uncategorized_count and uncategorized_count[0] > 0:
        folder_name = db.fetchone("SELECT title FROM folders WHERE idx = 0")
        folder_title = folder_name[0] if folder_name else "🗂Aralash"
        folders_with_tests.append((0, folder_title))
    
    # Fetch other folders that have at least one visible test
    all_folders = db.fetchall("SELECT idx, title FROM folders WHERE idx != 0 ORDER BY idx DESC")
    
    for folder_id, folder_title in all_folders:
        test_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = %s AND hide = 0", (folder_id,))
        if test_count and test_count[0] > 0:
            folders_with_tests.append((folder_id, folder_title))
    
    if folders_with_tests:
        await state.set_state(missing_hw_states.folders)
        await state.update_data(current_folder_page=1)
        await msg.edit_text(
            "Quyida arxivdagi mavzular:",
            reply_markup=get_folders_keyboard(folders_with_tests)
        )
    else:
        await msg.edit_text("Afsuski, hozirda arxivda testlar yo'q.")

@usrarch.callback_query(F.data.startswith("folder_page_"), missing_hw_states.folders)
async def navigate_folder_pages(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[2]  # prev or next
    data = await state.get_data()
    current_page = data.get("current_folder_page", 1)
    
    # Get folders with tests - identical logic as in show_archive
    folders_with_tests = []
    
    # Always include uncategorized folder if it has tests
    uncategorized_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = 0 AND hide = 0")
    if uncategorized_count and uncategorized_count[0] > 0:
        folder_name = db.fetchone("SELECT title FROM folders WHERE idx = 0")
        folder_title = folder_name[0] if folder_name else "🗂Aralash"
        folders_with_tests.append((0, folder_title))
    
    # Fetch other folders that have at least one visible test
    all_folders = db.fetchall("SELECT idx, title FROM folders WHERE idx != 0 ORDER BY idx DESC")
    
    for folder_id, folder_title in all_folders:
        test_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = %s AND hide = 0", (folder_id,))
        if test_count and test_count[0] > 0:
            folders_with_tests.append((folder_id, folder_title))
    
    # Calculate total pages
    other_folders = [f for f in folders_with_tests if f[0] != 0]
    total_pages = max(1, (len(other_folders) + config.MAX_FOLDERS_PER_PAGE - 1) // config.MAX_FOLDERS_PER_PAGE)
    
    if action == "prev":
        if current_page > 1:
            current_page -= 1
        else:
            await callback.answer("Siz allaqachon birinchi sahifadasiz.")
            return
    elif action == "next":
        if current_page < total_pages:
            current_page += 1
        else:
            await callback.answer("Siz allaqachon oxirgi sahifadasiz.")
            return
    else:
        await callback.answer("Hozirgi sahifani ko'rsatish uchun.")
        return
    
    await state.update_data(current_folder_page=current_page)
    
    try:
        await callback.message.edit_text(
            "Quyida arxivdagi mavzular:",
            reply_markup=get_folders_keyboard(folders_with_tests, current_page)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # The message is already showing the current page, no need to update
            pass
        else:
            # Some other error occurred
            raise

@usrarch.callback_query(F.data.startswith("folder_"), missing_hw_states.folders)
async def show_folder_exams(callback: types.CallbackQuery, state: FSMContext):
    # Make sure this isn't a page navigation command
    if callback.data.startswith("folder_page_"):
        return
        
    folder_id = int(callback.data.split("_")[1])
    await callback.message.edit_text("Yuklanmoqda...")
    
    # Fetch exams for the selected folder (newest to oldest)
    exams = db.fetchall(
        "SELECT title, idx FROM exams WHERE folder = %s AND hide = 0 ORDER BY idx DESC;",
        (folder_id,)
    )
    
    if exams:
        # Calculate total pages
        total_pages = max(1, (len(exams) + config.MAX_EXAMS_PER_PAGE - 1) // config.MAX_EXAMS_PER_PAGE)
        
        # Start at page 1 (newest exams)
        await state.update_data(current_exam_page=1, selected_folder=folder_id, total_exam_pages=total_pages)
        await state.set_state(missing_hw_states.exams)
        folder_name = db.fetchone("SELECT title FROM folders WHERE idx = %s", (folder_id,))
        folder_title = folder_name[0] if folder_name else "🗂Aralash"
        await callback.message.edit_text(
            f"📝 {html.bold(folder_title)} mavzusidagi vazifalar:",
            reply_markup=get_folder_exams(exams, 1)
        )
    else:
        # This shouldn't happen since we're only showing folders with tests,
        # but keeping it as a fallback
        all_folders_with_tests = []
        
        # Get all folders with tests again (same logic as in show_archive)
        uncategorized_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = 0 AND hide = 0")
        if uncategorized_count and uncategorized_count[0] > 0:
            folder_name = db.fetchone("SELECT title FROM folders WHERE idx = 0")
            folder_title = folder_name[0] if folder_name else "🗂Aralash"
            all_folders_with_tests.append((0, folder_title))
        
        all_folders = db.fetchall("SELECT idx, title FROM folders WHERE idx != 0 ORDER BY idx DESC")
        for fid, ftitle in all_folders:
            test_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = %s AND hide = 0", (fid,))
            if test_count and test_count[0] > 0:
                all_folders_with_tests.append((fid, ftitle))
        await callback.answer("Bu mavzuda vazifalar yo'q.")
        await callback.message.edit_text(
            "Bu mavzuda vazifalar yo'q. Boshqa mavzuni tanlang:",
            reply_markup=get_folders_keyboard(all_folders_with_tests, 1)
        )

@usrarch.callback_query(F.data.startswith("mexampage_"), missing_hw_states.exams)
async def navigate_exam_pages(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]  # prev or next
    data = await state.get_data()
    current_page = data.get("current_exam_page", 1)
    folder_id = data.get("selected_folder")
    
    # Fetch exams for the selected folder (newest to oldest)
    exams = db.fetchall(
        "SELECT title, idx FROM exams WHERE folder = %s AND hide = 0 ORDER BY idx DESC;",
        (folder_id,)
    )
    
    # Calculate total pages
    total_pages = max(1, (len(exams) + config.MAX_EXAMS_PER_PAGE - 1) // config.MAX_EXAMS_PER_PAGE)
    
    # Check if we're at page boundary and handle accordingly
    if action == "prev":
        if current_page < total_pages:
            current_page += 1
        else:
            await callback.answer("Siz allaqachon birinchi sahifadasiz.")
            return
    elif action == "next":
        if current_page > 1:
            current_page -= 1
        else:
            await callback.answer("Siz allaqachon oxirgi sahifadasiz.")
            return
    
    await state.update_data(current_exam_page=current_page)
    folder_name = db.fetchone("SELECT title FROM folders WHERE idx = %s", (folder_id,))
    folder_title = folder_name[0] if folder_name else "🗂Aralash"
    
    # Wrap edit_text in try-except to handle message not modified errors
    try:
        await callback.message.edit_text(
            f"📝 {html.bold(folder_title)} mavzusidagi vazifalar:",
            reply_markup=get_folder_exams(exams, current_page)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # The message is already showing the current page, no need to update
            pass
        else:
            # Some other error occurred
            raise

@usrarch.callback_query(F.data == "back_to_folders", missing_hw_states.exams)
async def back_to_folders(callback: types.CallbackQuery, state: FSMContext):
    # Get all folders with tests
    folders_with_tests = []
    
    # Always include uncategorized folder if it has tests
    uncategorized_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = 0 AND hide = 0")
    if uncategorized_count and uncategorized_count[0] > 0:
        folder_name = db.fetchone("SELECT title FROM folders WHERE idx = 0")
        folder_title = folder_name[0] if folder_name else "🗂Aralash"
        folders_with_tests.append((0, folder_title))
    
    # Fetch other folders that have at least one visible test
    all_folders = db.fetchall("SELECT idx, title FROM folders WHERE idx != 0 ORDER BY idx DESC")
    
    for folder_id, folder_title in all_folders:
        test_count = db.fetchone("SELECT COUNT(*) FROM exams WHERE folder = %s AND hide = 0", (folder_id,))
        if test_count and test_count[0] > 0:
            folders_with_tests.append((folder_id, folder_title))
    
    data = await state.get_data()
    current_page = data.get("current_folder_page", 1)
    
    await state.set_state(missing_hw_states.folders)
    await callback.message.edit_text(
        "Quyida arxivdagi mavzular:",
        reply_markup=get_folders_keyboard(folders_with_tests, current_page)
    )

# Keep existing handlers below
@usrarch.callback_query(F.data.startswith("mexam_"), missing_hw_states.exams)
async def start_missing_exam(callback: types.CallbackQuery, state: FSMContext):
    # Make sure this isn't a page navigation command
    if callback.data.startswith("mexampage_"):
        return
    
    # Get exam id from callback data
    await callback.message.edit_text("Yuklanmoqda...")
    try:
        exam_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri vazifa identifikatori.")
        return
        
    # Fetch exam using exam_id (deadline check removed)
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (exam_id,))
    if not test:
        await callback.message.answer("Vazifa topilmadi. Iltimos, admin bilan bog'laning.")
        return
    
    submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(callback.from_user.id), exam_id))
    if submission and not test[7]:
        await callback.message.answer("Bu vazifaga bir martadan ortiq javoblaringizni topshira olmaysiz!")
        return
    # Check if user already submitted (simple check without deadline logic)
    # submission = db.fetchone("SELECT  FROM submissions WHERE userid = %s AND exid = %s", (str(callback.from_user.id), exam_id))
    # if submission:
    #     await callback.message.answer("Siz bu vazifaga javoblaringizni allaqachon topshirgansiz.")
    #     return
    try:
        import json
        test_info = json.loads(test[5])
    except Exception:
        await callback.message.answer("Test tafsilotlarini yuklashda xatolik yuz berdi.", reply_markup=usr_main_key)
        return
    await state.update_data(
        exam_id=exam_id,
        ans_confirm=False,
        total=test[4],
        current=1,
        title=test[1],
        about=test[2],
        instructions=test[3],
        correct=test_info.get("answers", []),
        typesl=test_info.get("types", []),
        donel=[None]*test[4],
        page=1
    )
    current = 1
    attaches = db.fetchall("SELECT ty, tgfileid, caption FROM attachments WHERE exid = %s", (exam_id,))
    if attaches:
        for ty, tgfileid, caption in attaches:
            if ty == "photo":
                await callback.message.answer_photo(photo=tgfileid, caption=caption)
            elif ty == "document":
                await callback.message.answer_document(document=tgfileid, caption=caption)
    res = f"{get_user_text(test[1], test[2], test[3], test[4])}"
    await callback.message.answer(res, reply_markup=lets_start)
    # Transition state identical to regular HW
    await callback.message.delete()
    await state.set_state(missing_hw_states.details)

@usrarch.callback_query(F.data == "start_test", missing_hw_states.details)
async def start_test(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("Javoblarni qaysi yo'lda yuborishingizni tanlang.", reply_markup=ans_enter_method_usr)
    await state.set_state(missing_hw_states.way)

@usrarch.callback_query(F.data == "all", missing_hw_states.way)
async def all_at_once(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total")
    await state.update_data(entering="all")
    await callback.message.edit_text(f"Javoblaringizni quyidagi ko'rinishda jo'nating:\n{html.code('Javob1\nJavob2\nJavob3\n...')}")
    await state.set_state(missing_hw_states.answer)

@usrarch.callback_query(F.data == "one", missing_hw_states.way)
async def one_by_one(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(missing_hw_states.answer)
    await state.update_data(msg=callback.message.message_id)
    current = data.get("current")
    total = data.get("total")
    typesl = data.get("typesl")
    donel = data.get("donel")
    markup = get_answering_keys(current, total, donel, typesl, page=1)
    await callback.message.edit_text(
        f"\n{get_user_ans_text(donel, typesl)}\nIltimos, #{current}/{total} savol uchun javobingizni {html.underline('tanlang' if typesl[current-1] > 0 else 'jo\'nating')}:",
        reply_markup=markup
    )

@usrarch.callback_query(F.data.startswith("mcq_"), missing_hw_states.answer)
async def handle_mcq(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq") or data.get("current")
    typesl = data.get("typesl")
    if typesl[curq-1] == 0:
        await callback.answer("Bu variantli savol emas. Iltimos, javobingizni yuboring.", show_alert=True)
        return
    donel = data.get("donel")
    numq = data.get("total")
    cur_ans = callback.data.split("_")[1]
    donel[curq-1] = cur_ans
    ans_confirm = bool(data.get("ans_confirm"))
    await callback.answer(f"🟢 #{curq}: {cur_ans}")
    new_cur = next((i+1 for i, ans in enumerate(donel) if ans is None), -1)
    if new_cur == -1:
        ans_confirm = True
        await state.update_data(ans_confirm=ans_confirm)
    else:
        # Calculate new page based on the next question
        new_page = ((new_cur - 1) // config.MAX_QUESTION_IN_A_PAGE) + 1
        await state.update_data(curq=new_cur, donel=donel, page=new_page)

    current_page = data.get("page", 1) if new_cur == -1 else new_page
    prompt_text = html.underline("yuboring") if typesl[new_cur-1 if new_cur != -1 else curq-1] == 0 else html.underline("tanlang")
    try:
        await callback.message.edit_text(
            f"{get_user_ans_text(donel, typesl)}\n" +
            ("🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
            f"Iltimos, #{new_cur if new_cur != -1 else curq}/{numq} savol uchun javobingizni {prompt_text}:",
            reply_markup=get_answering_keys(new_cur if new_cur != -1 else curq, numq, donel, typesl, current_page, ans_confirm)
        )
    except Exception:
        await callback.answer("Iltimos, tugmalarni bitta-bittadan bosing.", show_alert=True)
        return

@usrarch.callback_query(F.data.startswith("jump_"), missing_hw_states.answer)
async def handle_jump(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_cur = int(callback.data.split("_")[1])
    curq = data.get("curq") or data.get("current")
    if new_cur == curq:
        await callback.answer("Siz allaqachon shu savolda turibsiz.")
        return
    donel = data.get("donel")
    typesl = data.get("typesl")
    numq = data.get("total")
    page = data.get("page")
    ans_confirm = bool(data.get("ans_confirm"))
    await state.update_data(curq=new_cur)
    prompt_text = html.underline("yuboring") if typesl[new_cur-1] == 0 else html.underline("tanlang")
    await callback.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\n" +
        ("🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{new_cur}/{numq} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(new_cur, numq, donel, typesl, page, ans_confirm)
    )

@usrarch.callback_query(F.data.startswith("page_"), missing_hw_states.answer)
async def handle_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total")
    donel = data.get("donel")
    typesl = data.get("typesl")
    page = data.get("page") or 1
    ans_confirm = bool(data.get("ans_confirm"))
    sign = callback.data.split("_")[1]
    max_page = (total + config.MAX_QUESTION_IN_A_PAGE - 1) // config.MAX_QUESTION_IN_A_PAGE
    if sign == "next":
        if page >= max_page:
            await callback.answer("Siz allaqachon oxirgi sahifadasiz.")
            return
        page += 1
    elif sign == "prev":
        if page <= 1:
            await callback.answer("Siz allaqachon birinchi sahifadasiz.")
            return
        page -= 1
    else:
        await callback.answer("Hozirgi sahifani ko'rsatish uchun.")
        return
    await state.update_data(page=page)
    curq = data.get("curq") or 1
    prompt_text = html.underline("yuboring") if typesl[curq-1] == 0 else html.underline("tanlang")
    await callback.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\n" +
        ("🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{curq}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(curq, total, donel, typesl, page, ans_confirm)
    )

@usrarch.message(missing_hw_states.answer)
async def handle_open_ended(message: types.Message, state: FSMContext):
    data = await state.get_data()
    typesl = data.get("typesl")
    curq = data.get("curq") or data.get("current")
    entering = data.get("entering")
    donel = data.get("donel")
    total = data.get("total")
    msg = data.get("msg")
    if entering=="all":
        if msg:
            await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=msg)
        raw = message.text
        cnt = raw.count("\n")
        if cnt != total-1:
            await message.reply(f"Iltimos, savollar soniga teng bo'lgan javob taqdim qiling. Sizning xabaringizda {cnt+1}/{total} ta javob bor.\n\nJavoblaringizni quyidagi ko'rinishda jo'nating:\n{html.code('Javob1\nJavob2\nJavob3\n...')}")
            return
        donel = list(filter(None, raw.split("\n")))
        print(donel)
        msg = await message.answer(f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob taqdim etdingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nAgar javoblaringizni o'zgartirmoqchi bo'lsangiz, yangi xabarda javoblaringizni quyidagi ko'rinishda jo'nating:\n{html.code('Javob1\nJavob2\nJavob3\n...')}",
            reply_markup=all_continue_usr)
        await state.update_data(donel=donel, msg=msg.message_id)
        return
    # ... existing all answers handling code ...

    if typesl[curq-1] > 0:
        await message.delete()
        msg = await message.answer("Bu ochiq savol emas. Iltimos, berilgan variantlardan birini tanlang.")
        sleep(2)
        await msg.delete()
        return

    donel[curq-1] = message.text
    new_cur = next((i+1 for i, ans in enumerate(donel) if ans is None), -1)
    await state.update_data(donel=donel)
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=msg, text=f"Iltimos, #{curq}/{total} savol uchun javobingizni jo'nating:")

    if new_cur == -1:
        current_page = data.get("page", 1)
        ans_confirm = True
        await state.update_data(ans_confirm=ans_confirm)
    else:
        # Calculate new page based on the next question
        current_page = ((new_cur - 1) // config.MAX_QUESTION_IN_A_PAGE) + 1
        await state.update_data(curq=new_cur, page=current_page)

    prompt_text = html.underline("yuboring") if typesl[new_cur-1 if new_cur != -1 else curq-1] == 0 else html.underline("tanlang")
    msg_resp = await message.answer(
        f"{get_user_ans_text(donel, typesl)}\n" +
        ("🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{new_cur if new_cur != -1 else curq}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(new_cur if new_cur != -1 else curq, total, donel, typesl, current_page, new_cur == -1)
    )
    await state.update_data(msg=msg_resp.message_id)

@usrarch.callback_query(F.data == "continue", missing_hw_states.answer)
async def request_submit_hw(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    donel = data.get("donel")
    typesl = data.get("typesl")
    await callback.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\nJavoblaringizni jo'natishni tasdiqlaysizmi?",
        reply_markup=submit_ans_user
    )
    await state.set_state(missing_hw_states.confirm)

@usrarch.callback_query(F.data == "submit", missing_hw_states.confirm)
async def confirm_submit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Kutib turing...")
    data = await state.get_data()
    submission_time = datetime.now(timezone(timedelta(hours=5)))
    exam_id = data.get("exam_id")
    # Fetch exam without deadline check
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (exam_id,))
    if not test:
        await callback.message.answer("Javobingizni saqlashni iloji yo'q! Iltimos, admin bilan bog'laning.", reply_markup=usr_main_key)
        await state.clear()
        return
    # submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(callback.from_user.id), exam_id))
    # if submission:
    #     await callback.message.answer("Siz allaqachon vazifaga javoblaringizni topshirib bo'lgansiz.")
    #     return
    correct = data.get("correct")
    answers = data.get("donel")
    code = gen_code(10)
    db.store_submission(callback.from_user.id, exam_id, answers, code, submission_time)
    await callback.answer("Muvaffaqiyatli jo'natildi.")
    await callback.message.edit_text(
        f"Vazifaga javoblaringiz muvaffaqiyatli topshirildi.\n\nNatijalaringiz:\n{get_correct_text(correct, answers)}",
        reply_markup=share_sub_usr(code)
    )
    await state.clear()

@usrarch.callback_query(F.data == "back", missing_hw_states.confirm)
async def cancel_submit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(missing_hw_states.answer)
    data = await state.get_data()
    curq = data.get("curq") or data.get("current")
    page = data.get("page")
    donel = data.get("donel")
    typesl = data.get("typesl")
    entering = data.get("entering")
    total = data.get("total")
    if entering == "all":
        await callback.message.edit_text(
            f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'lgansiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nAgar o'zgartirish kiritmoqchi bo'lsangiz, quyidagi formatda jo'nating:\n{html.code('Javob1\nJavob2\nJavob3\n...')}",
            reply_markup=all_continue_usr
        )
        return
    prompt_text = html.underline("yuboring") if typesl[curq-1] == 0 else html.underline("tanlang")
    await callback.message.edit_text(
        f"Topshirish bekor qilindi. Javob berishda davom eting.\n\n{get_user_ans_text(donel, typesl)}\n" +
        ("🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{curq}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(curq, total, donel, typesl, page, True)
    )