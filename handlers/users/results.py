from aiogram import types, Router, F, html
from filters import IsUser, IsUserCallback, IsSubscriber, IsSubscriberCallback
from loader import db
from data import dict
from aiogram.fsm.context import FSMContext
import json, logging
from time import sleep
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
    await message.answer(f"{html.bold(dict.results)} menyusi", reply_markup=usr_main_key)
    msg = await message.answer("Yuklanmoqda...")
    sub = db.fetchone("SELECT * FROM submissions WHERE userid = %s ORDER BY idx DESC LIMIT 1", (str(message.from_user.id),))
    if not sub:
        await msg.edit_text("Bu yerda sizning natijalaringiz bo'ladi. Hozircha natijalaringiz yo'q.")
        return
    await show_result(msg, sub)


async def show_result(message: types.Message, sub):
    exam_det = db.fetchone("SELECT title, correct, sdate FROM exams WHERE idx = %s", (sub[2],))
    if not exam_det:
        await message.answer("Ushbu natija topshirilgan imtihon o'chirib tashlangan. Boshqa natijalar qidirilmoqda...")
        query = "SELECT * FROM submissions WHERE idx < %s AND userid = %s ORDER BY idx DESC LIMIT 1"
        sub = db.fetchone(query, (sub[0], str(message.from_user.id),))
        if not sub:
            await message.answer("Boshqa natijalar topilmadi.")
        else:
            if await show_result(message, sub):
                await message.answer("Xatolik yuz berdi.")
        return 0
    
    # Proper timezone handling for both dates
    deadline_dt = exam_det[2]
    if deadline_dt:
        if deadline_dt.tzinfo is None:
            # If naive datetime, assume UTC and convert to UTC+5
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc).astimezone(UTC_OFFSET)
        else:
            # If already has timezone, ensure it's in UTC+5
            deadline_dt = deadline_dt.astimezone(UTC_OFFSET)
    
    sub_dt = sub[3]
    if sub_dt.tzinfo is None:
        # If naive datetime, assume UTC and convert to UTC+5
        sub_dt = sub_dt.replace(tzinfo=timezone.utc).astimezone(UTC_OFFSET)
    else:
        # If already has timezone, ensure it's in UTC+5
        sub_dt = sub_dt.astimezone(UTC_OFFSET)
    
    date_str = sub_dt.strftime('%H:%M:%S — %Y-%m-%d')
    exsub_time = ""
    if deadline_dt and sub_dt > deadline_dt:
        exsub_time = html.italic("\n⚠️ Vaqtidan keyin topshirilgan")
    ccode = sub[5]
    correct, answers = [], []
    try:
        correct = json.loads(exam_det[1])['answers']
        answers = json.loads(sub[4])
    except Exception as e:
        logging.error(f"Error parsing answers: {e}", exc_info=True)
        return 1
    # cnt = sum(a == b for a, b in zip(answers, correct))
    
    res = ""
    cnt = 0
    for i in range((len(correct)+1)//2):
        i1 = i
        i2 = (len(correct)+1)//2+i
        tex1 = f"{html.bold(i1+1)}. {html.code(answers[i1])} "
        tex2 = ""
        if type(correct[i1]) == list:
            print("here")
            if answers[i1] in correct[i1]:
                cnt += 1
                tex1 += "✅\t"
            else:
                tex1 += "❌\t"
        else:
            if correct[i1] == answers[i1]:
                cnt += 1
                tex1 += "✅\t"
            else:
                tex1 += "❌\t"
        if i2 != len(correct):
            tex2 = f"{html.bold(i2+1)}. {html.code(answers[i2])} "
            if type(correct[i2]) == list:
                if answers[i2] in correct[i2]:
                    cnt += 1
                    tex2 += "✅"
                else:
                    tex2 += "❌"
            else:
                if correct[i2] == answers[i2]:
                    cnt += 1
                    tex2 += "✅"
                else:
                    tex2 += "❌"
        res += tex1 + tex2 + "\n"
    result_text = (
        f"📝 {html.bold(exam_det[0])} uchun natija #{sub[0]}\n"
        f"⏰ Topshirilgan vaqti: {html.code(date_str)}{exsub_time}\n"
        f"✅ To'g'ri javoblar: {html.bold(f'{cnt}/{len(correct)}')} ({cnt/len(correct)*100:.1f}%)\n"
        f"📑 SAT taxminiy ball: {html.bold(int(round((cnt/len(correct)*600+200)/10))*10)}"
    )
    result_text += "\n\n" + html.expandable_blockquote("#Raq. Natija\n" + res)
    await message.edit_text(result_text, reply_markup=results_time(sub[0], ccode, 0))
    return 0


@reshow.callback_query(F.data.startswith("result_"), result_states.show)
async def navigate_results(callback: types.CallbackQuery):
    _, action, sub_id = callback.data.split('_')
    if action == 'earlier':
        query = "SELECT * FROM submissions WHERE idx < %s AND userid = %s ORDER BY idx DESC LIMIT 1"
    else:
        query = "SELECT * FROM submissions WHERE idx > %s AND userid = %s ORDER BY idx ASC LIMIT 1"

    sub = db.fetchone(query, (sub_id, str(callback.from_user.id),))
    if not sub:
        await callback.answer("Boshqa natijalar topilmadi.", show_alert=True)
    else:
        if await show_result(callback.message, sub):
            await callback.answer("Xatolik yuz berdi.", show_alert=True)
    await callback.answer()
