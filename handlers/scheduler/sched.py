from datetime import datetime
from data import config
from aiogram import types
from loader import scheduler, bot, db

async def send_in_future(pchid: int, text: str, markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | types.ForceReply | types.ReplyKeyboardRemove | None, prev: bool = True, disnoti: bool = False, rplytoid: int = None, wout_repl: bool = None, smid: int = None):
    try:
        msg = await bot.send_message(pchid, text, reply_markup=markup, disable_web_page_preview=prev, disable_notification=disnoti, reply_to_message_id=rplytoid, allow_sending_without_reply=wout_repl)
    except Exception as e:
        print(f"Error sending scheduled message: {e}")
        return  
    db.query("UPDATE messages SET status = 1 AND msgid = ? WHERE idx = ?", (smid, msg.message_id))
    for idx in config.ADMINS:
        await bot.send_message(idx, f"Scheduled message sent (ID: {smid})", reply_parameters=types.reply_parameters.ReplyParameters(chat_id=msg.chat.id, message_id=msg.message_id))
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]: Sent scheduled message to {pchid} (Scheduled message ID: {smid})")

def unschedule(job_id: int) -> None:
    scheduler.remove_job(job_id)
    db.query("DELETE FROM messages WHERE jid = ?", (job_id,))
    print(f"Unscheduled job {job_id}")

def schedule_message(text: str, when: datetime, markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | types.ForceReply | types.ReplyKeyboardRemove | None, disable_web_page_preview: bool = True, disable_notification: bool = False, reply_to_message_id: int = None, allow_sending_without_reply: bool = None) -> int:
    pchid = db.fetchone("SELECT chid FROM channel WHERE post > 0")
    if pchid is None:
        # print("No channel for scheduled messages")
        return -1
    pchid = pchid[0]
    job = scheduler.add_job(send_in_future, 'date', run_date=when, args=[pchid, text, markup, disable_web_page_preview, disable_notification, reply_to_message_id, allow_sending_without_reply])
    db.query("INSERT INTO messages (jid, date) VALUES (?, ?)", (job.id, when.strftime('%Y-%m-%d %H:%M:%S')))
    idx = db.fetchone("SELECT idx FROM messages WHERE jid = ?", (job.id,))[0]
    scheduler.modify_job(job.id, args=[pchid, text, markup, disable_web_page_preview, disable_notification, reply_to_message_id, allow_sending_without_reply, idx])

    print(f"[#{job.id}]: Scheduled message for chat id {pchid} at {when.strftime('%Y-%m-%d %H:%M:%S')}")
    return job.id