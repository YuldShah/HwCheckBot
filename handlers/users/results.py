from aiogram import types, Router, F, html
from filters import IsUser, IsUserCallback, IsSubscriber, IsSubscriberCallback
from loader import db
from data import dict
from aiogram.fsm.context import FSMContext
import json
from states import result_states
from keyboards.inline import share_sub_usr, results_time
from keyboards.regular import usr_main_key
from datetime import datetime, timedelta, timezone

reshow = Router()
reshow.message.filter(IsUser(), IsSubscriber())
reshow.callback_query.filter(IsUserCallback(), IsSubscriberCallback())

UTC_OFFSET = timezone(timedelta(hours=5))  # UTC+5 timezone

@reshow.message(F.text == dict.results)
async def results(message: types.Message, state: FSMContext):
    await state.set_state(result_states.show)
    msg = await message.answer("Yuklanmoqda...", reply_markup=usr_main_key)
    sub = db.fetchone("SELECT * FROM submissions ORDER BY idx DESC LIMIT 1")
    if not sub:
        await msg.edit_text("Bu yerda sizning natijalaringiz bo'ladi. Hozircha natijalaringiz yo'q.")
        return
    await show_result(msg, sub)


async def show_result(message: types.Message, sub):
    # await message.edit_text("Yuklanmoqda...")
    exam_det = db.fetchone("SELECT title, correct FROM exams WHERE idx = %s", (sub[2],))

    ccode = sub[5]

    correct, answers = [], []
    try:
        correct = json.loads(exam_det[1])['answers']
        answers = json.loads(sub[4])
    except Exception as e:
        await message.edit_text("Xatolik sodir bo'ldi")
        return
    cnt = sum(a == b for a, b in zip(answers, correct))

    date_str = sub[3].astimezone(UTC_OFFSET).strftime('%H:%M:%S — %Y-%m-%d')
    result_text = (
        f"📝 {html.bold(exam_det[0])} uchun natija #{sub[0]}\n"
        f"⏰ Topshirilgan vaqti: {html.code(date_str)}\n"
        f"✅ To'g'ri javoblar: {html.bold(f'{cnt}/{len(correct)}')} ({cnt/len(correct)*100:.1f}%)\n"
        f"📑 SAT taxminiy ball: {html.bold(int(round((cnt/len(correct)*600+200)/10))*10)}"
    )

    await message.edit_text(result_text, reply_markup=results_time(sub[0], ccode))


@reshow.callback_query(F.data.startswith("result_"), result_states.show)
async def navigate_results(callback: types.CallbackQuery):
    _, action, sub_id = callback.data.split('_')
    if action == 'earlier':
        query = "SELECT * FROM submissions WHERE idx < %s ORDER BY idx DESC LIMIT 1"
    else:
        query = "SELECT * FROM submissions WHERE idx > %s ORDER BY idx ASC LIMIT 1"

    sub = db.fetchone(query, (sub_id,))
    if not sub:
        await callback.answer("Boshqa natijalar topilmadi.", show_alert=True)
    else:
        await show_result(callback.message, sub)
    await callback.answer()
