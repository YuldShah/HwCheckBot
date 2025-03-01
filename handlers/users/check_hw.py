from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, confirm_inl_key, share_sub_usr
from keyboards.regular import main_key, back_key, usr_main_key
from filters import IsUser, IsUserCallback, IsRegistered, IsSubscriber, CbData
from aiogram.fsm.context import FSMContext
from states import check_hw_states
import json
from time import sleep
from datetime import datetime, timezone, timedelta
from loader import db
from utils.yau import get_correct_text, get_user_ans_text, get_user_text, gen_code
from keyboards.inline import usr_inline, adm_inline, lets_start, get_answering_keys, ans_enter_method_usr, submit_ans_user, all_continue_usr

chhw = Router()
chhw.message.filter(IsUser(), IsSubscriber())
chhw.callback_query.filter(IsUserCallback(), IsSubscriber())

@chhw.message(F.text == dict.do_todays_hw)
async def do_today_hw(message: types.Message, state: FSMContext):
    await message.answer(f"{html.bold(dict.do_todays_hw)} menyusi", reply_markup=usr_main_key)
    now = datetime.now(timezone(timedelta(hours=5)))
    today_date = now.date()
    # Fetch homework scheduled for today by comparing the date part of sdate
    test = db.fetchone("SELECT * FROM exams WHERE DATE(sdate) = %s", (today_date,))
    if not test:
        await message.answer("Bugungi vazifa hali yuklanmagan yoki mavjud emas. Agar bu xato deb o'ylasangiz, iltimos admin bilan bog'laning.")
        return
    exam_id = test[0]
    # Check if user already submitted
    submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(message.from_user.id), exam_id))
    if submission and not test[7]:
        await message.answer("Siz allaqachon vazifaga javoblaringizni topshirib bo'lgansiz va qayta topshirish mumkin emas.")
        return
    # Parse test info stored in JSON
    try:
        import json
        test_info = json.loads(test[5])
    except Exception:
        await message.answer("Test tafsilotlarini yuklashda xatolik yuz berdi.", reply_markup=usr_main_key)
        return
    await state.update_data(exam_id=exam_id, ans_confirm=False,
                            total=test[4], current=1, title=test[1], about=test[2], instructions=test[3],
                            correct=test_info.get("answers", []),
                            typesl=test_info.get("types", []),
                            donel=[None]*test[4], page=1)
    # Send first question based on type and attachments if any:
    current = 1
    attaches = db.fetchall("SELECT ty, tgfileid, caption FROM attachments WHERE exid = %s", (exam_id,))
    if attaches:
        for ty, tgfileid, caption in attaches:
            if ty == "photo":
                await message.answer_photo(photo=tgfileid, caption=caption)
            elif ty == "document":
                await message.answer_document(document=tgfileid, caption=caption)
    res = f"{get_user_text(test[1], test[2], test[3], test[4])}"
    await message.answer(res, reply_markup=lets_start)
    await state.set_state(check_hw_states.details)

@chhw.callback_query(CbData("start_test"), check_hw_states.details)
async def start_test(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup()
    await query.message.answer("Javoblarni qaysi yo'lda yuborishingizni tanlang.", reply_markup=ans_enter_method_usr)
    await state.set_state(check_hw_states.way)

@chhw.callback_query(F.data == "all", check_hw_states.way)
async def all_at_once(query: types.CallbackQuery, state: FSMContext):
    # await query.message.edit_reply_markup()
    data = await state.get_data()
    total = data.get("total")
    await state.update_data(entering="all")
    await query.message.edit_text(f"Javoblaringizni quyidagi ko'rinishda jo'nating:\n{html.code("Javob1\nJavob2\nJavob3\n...")}")
    await state.set_state(check_hw_states.answer)

@chhw.callback_query(F.data == "one", check_hw_states.way)
async def one_by_one(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(check_hw_states.answer)
    # await query.message.delete()
    await state.update_data(msg=query.message.message_id)
    current = data.get("current")
    total = data.get("total")
    typesl = data.get("typesl")
    donel = data.get("donel")
    markup = get_answering_keys(current, total, donel, typesl, page=1)
    # q_type = typesl[current-1]
    # Send proper prompt based on question type:
    await query.message.edit_text(f"\n{get_user_ans_text(donel, typesl)}\nIltimos, #{current}/{total} savol uchun javobingizni {html.underline("tanlang" if typesl[current-1] > 0 else "jo'nating")}:", reply_markup=markup)
    
@chhw.callback_query(F.data.startswith("mcq_"), check_hw_states.answer)
async def handle_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq") or data.get("current")
    typesl = data.get("typesl")
    # print(curq, typesl)
    if typesl[curq-1] == 0:
        await query.answer("Bu variantli savol emas. Iltimos, javobingizni yuboring.", show_alert=True)
        return
    # Optionally, uncomment to force MCQ mode:
    # typesl[curq-1] = config.MULTIPLE_CHOICE_DEF
    donel = data.get("donel")
    numq = data.get("total")  # changed from "numquest"
    page = data.get("page")
    cur_ans = query.data.split("_")[1]
    donel[curq-1] = cur_ans
    ans_confirm = bool(data.get("ans_confirm"))
    await query.answer(f"🟢 #{curq}: {cur_ans}")
    new_cur = -1
    for i, ans in enumerate(donel):
        if ans is None:
            new_cur = i+1
            break
    if new_cur == -1:
        ans_confirm = True
        await state.update_data(ans_confirm=ans_confirm)
        try:
            await query.message.edit_text(
                f"{get_user_ans_text(donel, typesl)}\n" +
                (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
                f"Iltimos, #{curq}/{numq} savol uchun javobingizni {html.underline('tanlang') if typesl[curq-1] > 0 else html.underline('yuboring')}:",
                reply_markup=get_answering_keys(curq, numq, donel, typesl, data.get("page"), ans_confirm)
            )
        except:
            await query.answer("Iltimos, tugmalarni bitta-bittadan bosing.", show_alert=True)
            return
        await state.update_data(donel=donel)
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    await state.update_data(curq=new_cur, donel=donel, page=new_page)
    if typesl[new_cur-1] == 0:
        prompt_verb = html.underline("yuboring")
    else:
        prompt_verb = html.underline("tanlang")
    try:
        await query.message.edit_text(
            f"{get_user_ans_text(donel, typesl)}\n" +
            (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
            f"Iltimos, #{new_cur}/{numq} savol uchun javobingizni {prompt_verb}:",
            reply_markup=get_answering_keys(new_cur, numq, donel, typesl, new_page, ans_confirm)
        )
    except:
        await query.answer("Iltimos, tugmalarni bitta-bittadan bosing.", show_alert=True)
        return


@chhw.callback_query(F.data.startswith("jump_"), check_hw_states.answer)
async def handle_jump(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_cur = int(query.data.split("_")[1])
    curq = data.get("curq") or data.get("current")
    if new_cur == curq:
        await query.answer("Siz allaqachon shu savolda turibsiz.")
        return
    donel = data.get("donel")
    typesl = data.get("typesl")
    numq = data.get("total")  # changed from "numquest"
    page = data.get("page")
    ans_confirm = bool(data.get("ans_confirm"))
    await state.update_data(curq=new_cur)
    if typesl[new_cur-1] == 0:
        prompt_text = html.underline("yuboring")
    else:
        prompt_text = html.underline("tanlang")
    await query.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\n" +
        (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{new_cur}/{numq} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(new_cur, numq, donel, typesl, page, ans_confirm)
    )

@chhw.callback_query(F.data.startswith("page_"), check_hw_states.answer)
async def handle_page(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total")  # now using total key
    donel = data.get("donel")
    typesl = data.get("typesl")
    page = data.get("page") or 1
    ans_confirm = bool(data.get("ans_confirm"))
    sign = query.data.split("_")[1]  # "next", "prev", or "now"
    from data import config
    max_page = (total + config.MAX_QUESTION_IN_A_PAGE - 1) // config.MAX_QUESTION_IN_A_PAGE
    if sign == "next":
        if page >= max_page:
            await query.answer("Siz allaqachon oxirgi sahifadasiz.")
            return
        page += 1
    elif sign == "prev":
        if page <= 1:
            await query.answer("Siz allaqachon birinchi sahifadasiz.")
            return
        page -= 1
    else:
        await query.answer("Hozirgi sahifani ko'rsatish uchun.")
        return
    await state.update_data(page=page)
    curq = data.get("curq") or 1
    if typesl[curq-1] == 0:
        prompt_text = html.underline("yuboring")
    else:
        prompt_text = html.underline("tanlang")
    await query.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\n" +
        (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{curq}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(curq, total, donel, typesl, page, ans_confirm)
    )

@chhw.message(check_hw_states.answer)
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
    
    
    if typesl[curq-1] > 0:
        await message.delete()
        msg = await message.answer("Bu ochiq savol emas. Iltimos, berilgan variantlardan birini tanlang.")
        sleep(2)
        await msg.delete()
        return
    
    

    donel = data.get("donel")
    page = data.get("page")
    ans_confirm = data.get("ans_confirm")
    donel[curq-1] = message.text
    new_cur = -1
    for i, ans in enumerate(donel):
        if ans is None:
            new_cur = i+1
            break
    await state.update_data(donel=donel)
    msg = data.get("msg")
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=msg, text=f"Iltimos, #{curq}/{data.get('total')} savol uchun javobingizni jo'nating:")
    if new_cur == -1:
        ans_confirm = True
        await state.update_data(ans_confirm=ans_confirm)
        if typesl[curq-1] == 0:
            prompt_text = html.underline("yuboring")
        else:
            prompt_text = html.underline("tanlang")
        msg_resp = await message.answer(
            f"{get_user_ans_text(donel, typesl)}\n" +
            (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
            f"Iltimos, #{curq}/{total} savol uchun javobingizni {prompt_text}:",
            reply_markup=get_answering_keys(curq, total, donel, typesl, data.get('page'), ans_confirm)
        )
        await state.update_data(msg=msg_resp.message_id)
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    await state.update_data(curq=new_cur, donel=donel, page=new_page)
    if typesl[new_cur-1] == 0:
        prompt_text = html.underline("yuboring")
    else:
        prompt_text = html.underline("tanlang")
    msg_resp = await message.answer(
        f"{get_user_ans_text(donel, typesl)}\n" +
        (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{new_cur}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(new_cur, total, donel, typesl, new_page, data.get("ans_confirm"))
    )
    await state.update_data(msg=msg_resp.message_id)

@chhw.callback_query(F.data == "continue", check_hw_states.answer)
async def request_submit_hw(query: types.CallbackQuery, state: FSMContext):
    # Ask for final confirmation before submission
    data = await state.get_data()
    donel = data.get("donel")
    typesl = data.get("typesl")
    await query.message.edit_text(f"{get_user_ans_text(donel, typesl)}\nJavoblaringizni jo'natishni tasdiqlaysizmi?", reply_markup=submit_ans_user)
    await state.set_state(check_hw_states.confirm)

@chhw.callback_query(F.data == "submit", check_hw_states.confirm)
async def confirm_submit(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text("Kutib turing...")
    data = await state.get_data()
    submission_time = datetime.now(timezone(timedelta(hours=5)))
    exam_id = data.get("exam_id")
    # Fetch exam using exam id
    test = db.fetchone("SELECT * FROM exams WHERE idx = %s", (exam_id,))
    if not test:
        await query.message.answer("Javobingizni saqlashni iloji yo'q!\n\nSiz topshirmoqchi bo'lgan vazifa vaqti o'tib ketganga yoki o'chirib tashlangan o'xshaydi.", reply_markup=usr_main_key)
        await state.clear()
        return
    # Check deadline: compare test deadline (sdate) with current time
    exam_deadline = datetime.fromisoformat(test[6])
    if submission_time > exam_deadline and not test[7]:
        await query.message.answer("Vaqt tugagan. Javoblaringiz qabul qilinmaydi.", reply_markup=usr_main_key)
        await state.clear()
        return
    submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(query.from_user.id), exam_id))
    if submission and not test[7]:
        await query.message.answer("Siz allaqachon vazifaga javoblaringizni topshirib bo'lgansiz va qayta topshirish mumkin emas.")
        return

    correct = data.get("correct")
    answers = data.get("donel")
    userid = query.from_user.id
    code = gen_code(10)
    db.store_submission(userid, exam_id, data.get("donel"), code, submission_time)
    await query.answer("Muvaffaqiyatli jo'natildi.")
    await query.message.edit_text(
        f"Vazifaga javoblaringiz muvaffaqiyatli topshirildi.\n\nNatijalaringiz quyidagicha:\n{get_correct_text(correct, answers)}",
        reply_markup=share_sub_usr(code)
    )
    await state.clear()

@chhw.callback_query(F.data == "back", check_hw_states.confirm)
async def cancel_submit(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(check_hw_states.answer)
    # await query.message.delete()
    data = await state.get_data()
    curq = data.get("curq") or data.get("current")
    page = data.get("page")
    donel = data.get("donel")
    typesl = data.get("typesl")
    entering = data.get("entering")
    total = data.get("total")
    if entering=="all":
        await query.message.edit_text(f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'lgansiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nAgar javoblaringizni o'zgartirmoqchi bo'lsangiz, yangi xabarda javoblaringizni quyidagi ko'rinishda jo'nating:\n{html.code('Javob1\nJavob2\nJavob3\n...')}", reply_markup=all_continue_usr)
        return
    
    if typesl[curq-1] == 0:
        prompt_text = html.underline("yuboring")
    else:
        prompt_text = html.underline("tanlang")
    await query.message.edit_text(
        f"Topshirish bekor qilindi. Javob berishda davom eting.\n\n{get_user_ans_text(donel, typesl)}\n" +
        (f"🔔 Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else "") +
        f"Iltimos, #{curq}/{total} savol uchun javobingizni {prompt_text}:",
        reply_markup=get_answering_keys(curq, total, donel, typesl, page, True)
    )