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