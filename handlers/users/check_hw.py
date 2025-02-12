from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, confirm_inl_key
from keyboards.regular import main_key, back_key
from filters import IsUser, IsUserCallback, IsRegistered, IsSubscriber
from aiogram.fsm.context import FSMContext
from states import check_hw_states
import json
from datetime import datetime, timezone, timedelta
from loader import db
from keyboards.inline import usr_inline, adm_inline, obom



chhw = Router()
chhw.message.filter(IsUser(), IsSubscriber())
chhw.callback_query.filter(IsUserCallback(), IsSubscriber())

@chhw.message(F.text == dict.do_todays_hw)
# @chhw.message(F.text == dict.do_hw)
async def do_today_hw(message: types.Message, state: FSMContext):
    # Get today's date in UTC+5
    today = datetime.now(timezone(timedelta(hours=5))).strftime("%d %m %Y")
    
    # Fetch homework test scheduled for today from storage
    test = db.fetchone("SELECT * FROM exams WHERE sdate = %s", (today,))
    if not test:
        await message.answer("Bugungi vazifa hali yuklangani yo'q yoki bugunga vazifa yo'q. Agar bu xato deb o'ylasangiz admin bilan bog'laning.")
        return

    exam_id = test[0]
    # Check if user already submitted
    submission = db.fetchone("SELECT * FROM submissions WHERE userid = %s AND exid = %s", (str(message.from_user.id), exam_id))
    if submission:
        await message.answer("Siz allaqachon vazifaga javoblaringizni topshirib bo'lgansiz.")
        return

    # Assume test[5] contains a JSON string with the correct answers and types, e.g.:
    # {"answers": ["A", "B", "Answer3", ...], "types": [config.MULTIPLE_CHOICE_DEF, 0, ...]}
    try:
        test_info = json.loads(test[5])
    except Exception:
        await message.answer("Homework data is corrupted.")
        return

    await state.update_data(exam_id=exam_id,
                            total=test[4],           # num_questions
                            current=1,
                            correct=test_info.get("answers", []),
                            types=test_info.get("types", []),
                            answers=[None]*test[4])
    # Send first question based on type:
    current = 1
    q_type = test_info.get("types", [])[current-1]
    if q_type and q_type > 0:
        # Use user's own MCQ keyboard instead of adm_inline.obom
        markup = usr_inline.create_mcq_keyboard(current, test[4], [None]*test[4], test_info.get("types", []), page=1)
        await message.answer(f"Question #{current} (MCQ): Please choose your answer:", reply_markup=markup)
    else:
        # Open ended question: send a plain prompt
        await message.answer(f"Question #{current} (Open ended): Please send your answer as message.")
    await state.set_state(check_hw_states.answer)

@chhw.callback_query(check_hw_states.answer)
async def process_mcq_answer(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("current")
    total = data.get("total")
    typesl = data.get("types")
    answers = data.get("answers")
    # Expect callback: format "user_mcq_{ANSWER}", e.g., "user_mcq_A"
    answer = query.data.split("_")[2]
    answers[current-1] = answer
    await state.update_data(answers=answers)
    
    # Move to next question if any
    if current < total:
        current += 1
        await state.update_data(current=current)
        q_type = typesl[current-1]
        if q_type and q_type > 0:
            markup = usr_inline.create_mcq_keyboard(current, total, answers, typesl, page=1)
            await query.message.edit_text(f"Question #{current} (MCQ): Please choose your answer:", reply_markup=markup)
        else:
            await query.message.edit_text(f"Question #{current} (Open ended): Please send your answer as message.")
    else:
        # All questions answered: ask for confirmation via inline button
        # confirm_markup = usr_inline.start_inline()  # reuse or build a confirm inline
        await query.message.edit_text("All answers received. Press Confirm to submit your homework.", reply_markup=confirm_inl_key)
        await state.set_state(check_hw_states.confirm)

@chhw.message(check_hw_states.answer)
async def process_open_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current")
    total = data.get("total")
    typesl = data.get("types")
    answers = data.get("answers")
    # Process open ended answer for open mode question only
    if typesl[current-1] == 0:
        answers[current-1] = message.text
        await state.update_data(answers=answers)
        if current < total:
            current += 1
            await state.update_data(current=current)
            q_type = typesl[current-1]
            if q_type and q_type > 0:
                markup = adm_inline.obom(current, total, answers, typesl, page=1)
                await message.answer(f"Question #{current} (MCQ): Please choose your answer:", reply_markup=markup)
            else:
                await message.answer(f"Question #{current} (Open ended): Please send your answer as message.")
        else:
            confirm_markup = usr_inline.start_inline()  # reuse confirm inline
            await message.answer("All answers received. Press Confirm to submit your homework.", reply_markup=confirm_markup)
            await state.set_state(check_hw_states.confirm)
    else:
        # Ignore open text if question is MCQ
        await message.answer("This question requires selecting an option via buttons.")

@chhw.callback_query(check_hw_states.confirm)
async def confirm_submission(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exam_id = data.get("exam_id")
    user_answers = data.get("answers")
    correct = data.get("correct")
    score = 0
    for ua, ca in zip(user_answers, correct):
        if ua and ua.lower() == ca.lower():
            score += 1
    # Save submission
    db.query("INSERT INTO submissions (userid, exid, answers) VALUES (%s, %s, %s)",
             (str(query.from_user.id), exam_id, json.dumps(user_answers)))
    await query.message.edit_text(f"Homework submitted successfully! Your score: {score}/{data.get('total')}")
    await state.clear()

# ...existing code...
