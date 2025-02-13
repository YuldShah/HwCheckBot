from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, confirm_inl_key
from keyboards.regular import main_key, back_key, usr_main_key
from filters import IsUser, IsUserCallback, IsRegistered, IsSubscriber, CbData
from aiogram.fsm.context import FSMContext
from states import check_hw_states
import json
from time import sleep
from datetime import datetime, timezone, timedelta
from loader import db
from utils.yau import get_correct_text, get_user_ans_text, get_user_text
from keyboards.inline import usr_inline, adm_inline, lets_start, get_answering_keys, ans_enter_method_usr, submit_ans_user

chhw = Router()
chhw.message.filter(IsUser(), IsSubscriber())
chhw.callback_query.filter(IsUserCallback(), IsSubscriber())

@chhw.message(F.text == dict.do_todays_hw)
async def do_today_hw(message: types.Message, state: FSMContext):
    # Get today's date in UTC+5
    await message.answer("Yuklanmoqda...", reply_markup=usr_main_key)
    today = datetime.now(timezone(timedelta(hours=5))).strftime("%d %m %Y")
    # Fetch homework test scheduled for today from storage
    test = db.fetchone("SELECT * FROM exams WHERE sdate = %s", (today,))
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
    await state.update_data(exam_id=exam_id,
                            total=test[4], current=1, title=test[1], about=test[2], instructions=test[3],
                            correct=test_info.get("answers", []),
                            typesl=test_info.get("types", []),
                            donel=[None]*test[4])
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
    q_type = typesl[current-1]
    # Send proper prompt based on question type:
    if q_type and q_type > 0:
        await query.message.edit_text(f"\n{get_user_ans_text(donel, typesl)}\nIltimos, #{current}/{total} savol uchun javobingizni tanlang:", reply_markup=markup)
    else:
        await query.message.edit_text(f"\n{get_user_ans_text(donel, typesl)}\nIltimos, #{current}/{total} savol uchun javobingizni tanlang:", reply_markup=markup)

@chhw.callback_query(F.data.startswith("mcq_"), check_hw_states.answer)
async def handle_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq") or data.get("current")
    typesl = data.get("typesl")
    from data import config
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
        new_cur=1
        new_page=1
        await state.update_data(ans_confirm=ans_confirm)
        await query.message.edit_text(f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nIltimos, #{new_cur}/{numq} savol uchun javobingizni tanlang:",
        reply_markup=get_answering_keys(new_cur, numq, donel, typesl, new_page, ans_confirm))
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    await state.update_data(curq=new_cur, donel=donel, page=new_page)
    await query.message.edit_text(f"{get_user_ans_text(donel, typesl)}\nIltimos, #{new_cur}/{numq} savol uchun javobingizni {html.underline("tanlang" if typesl[new_cur-1] > 0 else "jo'nating")}:",
        reply_markup=get_answering_keys(new_cur, numq, donel, typesl, new_page, ans_confirm)
    )

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
        await query.message.edit_text(
            f"{get_user_ans_text(donel, typesl)}\n{f"Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else ""}Iltimos, #{new_cur}/{numq} savol uchun javobingizni yuboring:",
            reply_markup=get_answering_keys(new_cur, numq, donel, typesl, page, ans_confirm)
        )
    else:
        await query.message.edit_text(
            f"{get_user_ans_text(donel, typesl)}\n{f"Barcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\n" if not donel.count(None) else ""}Iltimos, #{new_cur}/{numq} savol uchun javobingizni tanlang:",
            reply_markup=get_answering_keys(new_cur, numq, donel, typesl, page, ans_confirm)
        )

@chhw.callback_query(F.data.startswith("page_"), check_hw_states.answer)
async def handle_page(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("total")  # now using total key
    donel = data.get("donel")
    typesl = data.get("typesl")
    page = data.get("page") or 1
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
    await query.message.edit_text(
        f"{get_user_ans_text(donel, typesl)}\nDavom etmoqda - joriy sahifa: {page}",
        reply_markup=get_answering_keys(data.get("curq") or 1, total, donel, typesl, page, bool(data.get("ans_confirm")))
    )

@chhw.message(check_hw_states.answer)
async def handle_open_ended(message: types.Message, state: FSMContext):
    data = await state.get_data()
    typesl = data.get("typesl")
    curq = data.get("curq") or data.get("current")
    if typesl[curq-1] > 0:
        await message.delete()
        msg = await message.answer("Bu ochiq savol emas. Iltimos, berilgan variantlardan birini tanlang.")
        sleep(2)
        await msg.delete()
        return
    
    entering = data.get("entering")

    if entering=="all":
        donel = data.get("donel")
        donel[curq-1] = message.text
        new_cur = -1
        for i, ans in enumerate(donel):
            if ans is None:
                new_cur = i+1
                break
        await state.update_data(donel=donel)
        msg = data.get("msg")
        await message.bot.edit_message_text(message.chat.id, msg, f"Iltimos, #{curq}/{data.get('total')} savol uchun javobingizni jo'nating:")
        if new_cur == -1:
            ans_confirm = True
            new_cur=1
            new_page=1
            await state.update_data(ans_confirm=ans_confirm)
            await message.answer(f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nIltimos, #{new_cur}/{data.get("total")} savol uchun javobingizni tanlang:",
            reply_markup=get_answering_keys(new_cur, data.get("total"), donel, typesl, new_page, ans_confirm))
            return
        new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
        await state.update_data(curq=new_cur, donel=donel, page=new_page)
        await message.answer(f"{get_user_ans_text(donel, typesl)}\nIltimos, #{new_cur}/{data.get("total")} savol uchun javobingizni tanlang:",
            reply_markup=get_answering_keys(new_cur, data.get("total"), donel, typesl, new_page, ans_confirm)
        )
        return

    donel = data.get("donel")
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
        new_cur=1
        new_page=1
        await state.update_data(ans_confirm=ans_confirm)
        await message.answer(f"{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nIltimos, #{new_cur}/{data.get("total")} savol uchun javobingizni tanlang:",
        reply_markup=get_answering_keys(new_cur, data.get("total"), donel, typesl, new_page, ans_confirm))
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    await state.update_data(curq=new_cur, donel=donel, page=new_page)
    await message.answer(f"{get_user_ans_text(donel, typesl)}\nIltimos, #{new_cur}/{data.get("total")} savol uchun javobingizni tanlang:",
        reply_markup=get_answering_keys(new_cur, data.get("total"), donel, typesl, new_page, ans_confirm)
    )
    # await message.answer(f"#{curq} savoliga javob qabul qilindi.")
    # Optionally, proceed to next unanswered question or prompt submission...

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
    today = datetime.now(timezone(timedelta(hours=5))).strftime("%d %m %Y")
    test = db.fetchone("SELECT * FROM exams WHERE sdate = %s", (today,))
    if not test:
        await query.message.answer("Siz topshirmoqchi bo'lgan vazifa o'chirib tashlanganga o'xshaydi.")
        await state.clear()
        return
    exam_id = test[0]
    # Check if user already submitted
    submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(query.from_user.id), exam_id))
    if submission and not test[7]:
        await query.message.answer("Siz allaqachon vazifaga javoblaringizni topshirib bo'lgansiz va qayta topshirish mumkin emas.")
        return
    
    data = await state.get_data()
    correct = data.get("correct")
    exam_id = data.get("exam_id")
    answers = data.get("donel")
    userid = query.from_user.id
    # Store the submission in DB (assumes store_submission is defined accordingly)
    db.store_submission(userid, exam_id, data.get("donel"))
    await query.answer("Muvaffaqiyatli jo'natildi.")
    await query.message.edit_text(f"Vazifaga javoblaringiz muvaffaqiyatli topshirildi.\nNatijalaringiz quyidagicha:\n{get_correct_text(correct, answers)}")
    await state.clear()

@chhw.callback_query(F.data == "back", check_hw_states.confirm)
async def cancel_submit(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(check_hw_states.answer)
    # await query.message.delete()
    data = await state.get_data()
    donel = data.get("donel")
    typesl = data.get("typesl")
    await query.message.edit_text(f"Topshirish bekor qilindi. Javob berishda davom eting.\n\n{get_user_ans_text(donel, typesl)}\nBarcha savollarga javob berib bo'ldingiz, javobingizni topshirishni davom ettirsangiz bo'ladi.\n\nIltimos, #{1}/{data.get("total")} savol uchun javobingizni tanlang:",
        reply_markup=get_answering_keys(1, data.get("total"), donel, typesl, 1, 1))