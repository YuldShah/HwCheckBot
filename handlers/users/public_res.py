from aiogram import Router, F, types, html
from data import dict
from loader import db
from datetime import timezone, timedelta, datetime
import json


pub = Router()

UTC_OFFSET = timezone(timedelta(hours=5))  # UTC+5 timezone


@pub.inline_query(F.query.startswith("sub_"))
async def search_results(query: types.InlineQuery):
    sub_code = query.query.split("_")[1]
    sub = db.fetchone("SELECT * FROM submissions WHERE random = %s", (sub_code,))
    if not sub:
        res = types.InlineQueryResultArticle(
            id="no_result",
            title="🚫 Natija topilmadi",
            input_message_content=types.InputTextMessageContent(
                message_text="🚫 Siz qidirgan natija topilmadi."
            )
        )
        return await query.answer([res], cache_time=1, is_personal=True, switch_pm_parameter="myres", switch_pm_text="📊 Natijalarimni botda ko'rish")
    exam_det = db.fetchone("SELECT title, correct, sdate FROM exams WHERE idx = %s", (sub[2],))
    
    # Properly handle deadline timestamp (backend in UTC)
    deadline_dt = exam_det[2]
    if deadline_dt:
        if deadline_dt.tzinfo is None:
            # If naive datetime, assume UTC
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
        # Convert to UTC+5 for display
        deadline_display = deadline_dt.astimezone(UTC_OFFSET)
    else:
        deadline_display = None
    
    # Handle submission timestamp (backend in UTC)
    sub_dt = sub[3]
    if sub_dt.tzinfo is None:
        # If naive datetime, assume UTC
        sub_dt = sub_dt.replace(tzinfo=timezone.utc)
    # Convert to UTC+5 for display
    sub_display = sub_dt.astimezone(UTC_OFFSET)
    
    # Format the time in UTC+5 for display
    sub_time = sub_display.strftime('%H:%M:%S — %Y-%m-%d')
    
    exsub_time = ""
    if deadline_dt and sub_dt > deadline_dt:  # Compare in UTC for backend logic
        exsub_time = html.italic("\n⚠️ Vaqtidan keyin topshirilgan")
        
    title_of_exam = exam_det[0] if exam_det else "O'chirilgan test"
    user_name = db.fetchone("SELECT fullname FROM users WHERE userid = %s", (sub[1],))
    if not user_name:
        user_name = "Noma'lum"
    else:
        user_name = user_name[0]
    cnt = 0
    correct = json.loads(exam_det[1]).get("answers", [])
    answers = json.loads(sub[4])
    for i in range(len(correct)):
        if type(correct[i]) == list:
            if answers[i] in correct[i]:
                cnt += 1
        else:
            if answers[i] == correct[i]:
                cnt += 1
    ter = (
        f"📝 {html.bold(title_of_exam)} uchun natija {html.bold(f'#{sub[0]}')}"
        f"\n\n👤 Egasi: {html.bold(query.from_user.mention_html() if str(query.from_user.id) == sub[1] else html.link(user_name, f'tg://user?id={sub[1]}'))}"
        f"\n⏰ Topshirilgan vaqti: {html.code(sub_time)}{exsub_time}"
        f"\n✅ To'g'ri javoblar: {html.bold(f'{cnt}/{len(correct)}')} - {html.bold(f'{cnt/len(correct)*100:.1f}%')}"
        f"\n📑 SAT taxminiy ball: {html.bold(int(round((cnt/len(correct)*600+200)/10))*10)}"
    )
    res = types.InlineQueryResultArticle(
        id=sub_code,
        title=f"📊 Natijani ulashish",
        description=f"📝 {title_of_exam} uchun natija #{sub[0]}",
        input_message_content=types.InputTextMessageContent(
            message_text=ter
        )
    )
    return await query.answer([res], cache_time=1, is_personal=True)