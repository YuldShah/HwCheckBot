from aiogram import html
from aiogram.fsm.context import FSMContext
from loader import bot
from data import config

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
    data=await state.get_data()
    print(data)
    title=data.get("title")
    about=data.get("about")
    instructions=data.get("instructions")
    numquest=data.get("numquest")
    sdate=data.get("sdate")
    # duration=data.get("duration")
    res = ""
    res += f"{html.italic("Title:")} {title}\n" if title else ""
    res += f"{html.italic("Description:")} {html.expandable_blockquote(about)}\n" if about else ""
    res += f"{html.italic("Instructions:")} {html.expandable_blockquote(instructions)}\n" if instructions else ""
    res += f"{html.italic("Attachments:")} {html.bold(f'{len(data.get("attaches"))}')}\n" if data.get("attaches") else ""
    res += f"{html.italic("Number of questions:")} {html.bold(numquest)}\n" if numquest else ""
    res += f"{html.italic("Running date:")} {html.bold(sdate)}\n" if sdate else ""
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

def get_user_text(title, about, instructions, numquest):
    res = ""
    res += f"{html.italic('Nomi')}: {html.bold(title)}\n" if title else ""
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
            if type(donel[i]) == list:
                res += f" {html.code(f"{','.join(donel[i])}")}"
            else:
                res += f" {html.code(f"{donel[i]}")}"
        if typesl[i] == 0:
            res += " | OS"
        else:
            res += f" | V[{typesl[i]}]"
            cnt += 1
        res += "\n"
    res = f"✅ Javob berildi: {cnt}/{numq}\n\n#Raq. Javob | Turi\n" + res
    return html.expandable_blockquote(res)