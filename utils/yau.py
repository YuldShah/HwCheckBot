from aiogram import html
from aiogram.fsm.context import FSMContext
from loader import bot, db
from data import config
import logging
from datetime import timezone, timedelta

async def checksub(userid, chid):
    try:
        member = await bot.get_chat_member(chat_id=chid, user_id=userid)
    except Exception:
        for adm in config.ADMINS:
            chat_title = (await bot.get_chat(chid)).title
            await bot.send_message(adm, f"Error while checking subscribtion in {chat_title}. Looks like bot is not an admin in the chat.")
        return True
    return member.status in ["member", "creator", "owner", "administrator"]

async def get_text(state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    about = data.get("about")
    instructions = data.get("instructions")
    numquest = data.get("numquest")
    sdate = data.get("sdate")
    # duration=data.get("duration")
    res = ""
    res += f"{html.italic('Title:')} {title}\n" if title else ""
    res += f"{html.italic('Code:')} {html.code(data.get('code'))}\n" if data.get('code') else ""
    res += f"{html.italic('Description:')} {html.expandable_blockquote(about)}\n" if about else ""
    res += f"{html.italic('Instructions:')} {html.expandable_blockquote(instructions)}\n" if instructions else ""
    res += f"{html.italic('Attachments:')} {html.bold(f'{len(data.get("attaches"))}')}\n" if data.get("attaches") else ""
    res += f"{html.italic('Number of questions:')} {html.bold(numquest)}\n" if numquest else ""
    res += f"{html.italic('Deadline:')} {html.bold(sdate)}\n" if sdate else ""
    # res += f"Duration: {html.bold(duration)} minutes\n" if duration else ""
    return res

def get_ans_text(donel, typesl):
    numq = len(donel)
    res = ""
    cnt = 0
    for i in range(numq):
        res += f"{html.bold(f"{i+1}.")}"
        if donel[i]:
            if type(donel[i]) == list:
                res += f" {html.code(f"{','.join(donel[i])}")} "
            else:
                res += f" {html.code(f"{donel[i]}")} "
            if typesl[i] == 0:
                res += "| OE"
            else:
                res += f"| MCQ[{typesl[i]}]"
            cnt += 1
        res += "\n"
    res = f"✅ Done: {cnt}/{numq}\n\n#No. Ans | Type\n" + res
    return html.expandable_blockquote(res)

def get_user_text(title, about, instructions, numquest, code=None):
    res = ""
    res += f"{html.italic('Nomi')}: {html.bold(title)}\n" if title else ""
    res += f"{html.italic('Kodi')}: {html.code(code)}\n" if code else ""
    res += f"{html.italic('Izoh')}: {html.expandable_blockquote(about)}\n" if about else ""
    res += f"{html.italic("Yo'llanma")}: {html.expandable_blockquote(instructions)}\n" if instructions else ""
    res += f"{html.italic('Savollar soni')}: {html.bold(numquest)}\n" if numquest else ""
    return res

def get_user_ans_text(donel, typesl):
    numq = len(donel)
    res = ""
    cnt = 0
    for i in range(numq):
        res += f"{html.bold(f"{i+1}.")}"
        if donel[i]:
            cnt += 1
            if type(donel[i]) == list:
                res += f" {html.code(f"{','.join(donel[i])}")}"
            else:
                res += f" {html.code(f"{donel[i]}")}"
        if typesl[i] == 0:
            res += " | OS"
        else:
            res += f" | V[{typesl[i]}]"
        res += "\n"
    res = f"✅ Javob berildi: {cnt}/{numq}\n\n#Raq. Javob | Turi\n" + res
    return html.expandable_blockquote(res)

def get_correct_text(correct, answers):
    res = ""
    print(correct, answers)
    cnt = 0
    for i in range((len(correct)+1)//2):
        i1 = i
        i2 = (len(correct)+1)//2+i
        # print(i1, i2)
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
    res = html.expandable_blockquote(f"✅ To'g'ri javoblar: {html.bold(f"{cnt}/{len(correct)}")} - {html.bold(f"{cnt/len(correct)*100:.1f}%")}\n📑 SAT taxminiy ball: {html.bold(int(round((cnt/len(correct)*600+200)/10))*10)}\n#Raq. Natija\n" + res)
    return res

def gen_code(length):
    import random
    import string
    letters = string.ascii_letters
    digits = string.digits
    return ''.join(random.choice(letters + digits) for i in range(length))

# Test share codes: uppercase + digits minus look-alikes (I/1, O/0).
TEST_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TEST_CODE_LENGTH = 4

def normalize_test_code(raw):
    if not raw:
        return ""
    return "".join(ch for ch in str(raw).upper() if ch in TEST_CODE_ALPHABET)

def gen_test_code(db, length=TEST_CODE_LENGTH, attempts=200):
    import random
    for _ in range(attempts):
        code = ''.join(random.choice(TEST_CODE_ALPHABET) for _ in range(length))
        if not db.fetchone("SELECT idx FROM exams WHERE code = %s", (code,)):
            return code
    return gen_test_code(db, length + 1, attempts)

def score_submission(correct, answers):
    """Count correct answers. A key may be a list when several answers are accepted."""
    cnt = 0
    for c, a in zip(correct, answers):
        if isinstance(c, list):
            if a in c:
                cnt += 1
        elif c == a:
            cnt += 1
    return cnt

async def notify_admins_submission(user, exam, correct, answers, submitted_at, sub_code=None):
    """Tell every admin about a submission (admin side is English).

    Never raises: a failed notification must not break the user's submit.
    """
    try:
        from keyboards.inline import submission_admin_kb
        total = len(correct) or 1
        cnt = score_submission(correct, answers)
        pct = cnt / total * 100
        sat = int(round((cnt / total * 600 + 200) / 10)) * 10
        when = submitted_at
        if when is not None and when.tzinfo is not None:
            when = when.astimezone(timezone(timedelta(hours=5)))
        stamp = when.strftime('%H:%M - %d.%m.%Y') if when else '-'
        uname = f'@{user.username}' if user.username else 'no username'
        code = exam[11] if len(exam) > 11 and exam[11] else '-'
        late = ''
        deadline = exam[6]
        if deadline is not None and submitted_at is not None:
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if submitted_at > deadline:
                late = ' \u23f0 LATE'
        sub_id = None
        if sub_code:
            row = db.fetchone('SELECT idx FROM submissions WHERE random = %s', (sub_code,))
            sub_id = row[0] if row else None
        lines = [
            f"📥 {html.bold('New submission')}{late}",
            '',
            f'👤 {html.link(user.full_name, f"tg://user?id={user.id}")} ({uname})',
            f'🆔 {html.code(user.id)}',
            f'📝 {html.bold(exam[1])}',
            f'🔑 {html.code(code)}',
            f"✅ Score: {html.bold(f'{cnt}/{total}')} ({pct:.1f}%)",
            f'📑 Est. SAT: {html.bold(sat)}',
            f'🕒 {stamp} (UTC+5)',
        ]
        text = '\n'.join(lines)
        kb = submission_admin_kb(sub_id, sub_code, getattr(user, 'id', None))
        for adm in config.ADMINS:
            try:
                await bot.send_message(adm, text, reply_markup=kb, disable_web_page_preview=True)
            except Exception:
                logging.error(f'submission notify failed for admin {adm}', exc_info=True)
    except Exception:
        logging.error('notify_admins_submission failed', exc_info=True)
