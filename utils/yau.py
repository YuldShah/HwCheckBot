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
    res += f"{html.italic("Number of questions:")} {html.bold(numquest)}\n" if numquest else ""
    res += f"{html.italic("Start date:")} {html.bold(sdate)}\n" if sdate else ""
    # res += f"Duration: {html.bold(duration)} minutes\n" if duration else ""
    return res

def get_ans_text(donel, typesl):
    numq = len(donel)
    res = ""
    for i in range(numq):
        res += f"{html.bold(f"{i+1}.")} {html.code(f"{donel[i]}")} "
        if typesl[i] == 0:
            res += "| OE"
        else:
            res += f"| MCQ[{typesl[i]}]"
        res += "\n"
    return html.expandable_blockquote(res)