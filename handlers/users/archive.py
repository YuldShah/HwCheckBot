from aiogram import Router, F, html, types
from filters import IsUser, IsSubscriber, IsUserCallback, IsSubscriberCallback, IsArchiveAllowed, IsArchiveAllowedCallback
from data import dict, config
from loader import db
from aiogram.fsm.context import FSMContext
from keyboards.regular import usr_main_key
from keyboards.inline import lets_start, ans_enter_method_usr, goto_bot, submit_ans_user, all_continue_usr, get_missing_exams, get_answering_keys, share_sub_usr
from datetime import datetime, timezone, timedelta
from states import missing_hw_states
from utils.yau import get_user_text, get_user_ans_text, get_correct_text, gen_code

usrarch = Router()
usrarch.message.filter(IsUser(), IsSubscriber())
usrarch.callback_query.filter(IsUserCallback(), IsSubscriberCallback())

@usrarch.message(F.text == dict.archive)
async def show_archive(message: types.Message, state: FSMContext):
    await message.answer(f"{html.bold(dict.archive)} menyusi", reply_markup=usr_main_key)
    msg = await message.answer("Yuklanmoqda...")
    mexams = db.fetchall("SELECT title, idx FROM exams WHERE hide = 0;")
    if mexams:
        await state.set_state(missing_hw_states.exams)
        await msg.edit_text(f"Hozirda arxivda {len(mexams)} ta vazifalar mavjud. Quyida ro'yxat keltirilgan. Ulardan birini tanlang va bajarishni boshlang:", reply_markup=get_missing_exams(mexams))
    else:
        await msg.edit_text("Afsuski, hozirda arxivga ulashilgan testlar yo'q.")

# @usrarch.callback_query(F.data == "get_arch")
# async def get_archive(callback: types.CallbackQuery):
#     await callback.answer("Sizda allaqachon arxiv ruxsati bor.")
#    await callback.bot.edit_message_text(text="🎉 Sizda allaqachon arxiv ruxsati bor.", inline_message_id=callback.inline_message_id, reply_markup=goto_bot(config.bot_info.username))

@usrarch.callback_query(F.data.startswith("mexam_"), missing_hw_states.exams)
async def start_missing_exam(callback: types.CallbackQuery, state: FSMContext):
    # Get exam id from callback data
    await callback.message.edit_text("Yuklanmoqda...")
    exam_id = int(callback.data.split("_")[1])
    # Fetch exam using exam_id (deadline check removed)
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (exam_id,))
    if not test:
        await callback.message.answer("Vazifa topilmadi. Iltimos, admin bilan bog'laning.")
        return
    if not test[7]:
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

    # ... existing all answers handling code ...

    if typesl[curq-1] > 0:
        await message.delete()
        tmp = await message.answer("Bu ochiq savol emas. Iltimos, berilgan variantlardan birini tanlang.")
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