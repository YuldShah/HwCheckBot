from aiogram import Router, F, types, html
from data import dict
from loader import db
import json


pub = Router()


@pub.inline_query(F.query.startswith("sub_"))
async def search_results(query: types.InlineQuery):
    sub_code = query.query.split("_")[1]
    sub = db.fetchone("SELECT * FROM submissions WHERE random = %s", (sub_code,))
    if not sub:
        res = types.InlineQueryResultsButton(
            title="No results",
            description="No results found",
            input_message_content=types.InputTextMessageContent(
                message_text="No results found"
            )
        )
        return await query.answer([res], cache_time=1, is_personal=True)
    exam_det = db.fetchone("SELECT title, correct FROM exams WHERE idx = %s", (sub[2],))
    title_of_exam = None

    user_name = db.fetchone("SELECT fullname FROM users WHERE userid = %s", (sub[1],))
    if not user_name:
        user_name = "Anonim"
    else:
        user_name = user_name[0]
    if not exam_det:
        title_of_exam = "O'chirilgan test"
    else:
        title_of_exam = exam_det[0]
    cnt = 0
    correct = json.loads(exam_det[1]).get("answers", [])
    answers = json.loads(sub[4])

    for i in range(len(correct)):
        if answers[i] == correct[i]:
            cnt += 1
    ter = (
        f"📝 {html.bold(title_of_exam)} uchun natija {html.bold(f'#{sub[0]}')}"
        f"\n\n👤 Egasi: {html.bold(html.link(user_name, f'tg://user?id={sub[1]}'))}"
        f"\n⏰ Topshirilgan vaqti: {html.code(sub[3].strftime('%H:%M:%S — %Y-%m-%d'))}"
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