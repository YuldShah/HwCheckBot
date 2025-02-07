from aiogram import types, Router, F, html
from data import config
from keyboards.inline import perm_inl, grant_perm_to, goto_bot
# import hashlib
from time import sleep
from filters import InlineData, InlineDataStartsWith, IsAdmin, IsAdminCallback, IsAdminInline, CbData, CbDataStartsWith

allow = Router()

allow.message.filter(IsAdmin())
allow.callback_query.filter(IsAdminCallback())
allow.inline_query.filter(IsAdminInline())




@allow.inline_query(InlineData("allow"))
async def allow_inline(inline: types.InlineQuery):
    # unique_id = hashlib.md5(str(inline.from_user.id).encode()).hexdigest()
    res = types.InlineQueryResultArticle(
        id="wtf",
        title="Granting permission",
        description="Reply to the user's message to grant permission and click here",
        input_message_content=types.InputTextMessageContent(
            message_text="You need to fetch data about user to grant permission"
        ),
        reply_markup=perm_inl
    )
    msg = await inline.answer([res], cache_time=1, is_personal=True)


@allow.callback_query(CbData("fetch_data"))
async def fetch_data(callback: types.CallbackQuery):
    if callback.message.reply_to_message:
        userid = callback.message.reply_to_message.from_user.id
        mention = callback.message.reply_to_message.from_user.mention_html()
        res = f"User: {html.bold(f"{mention}")}\nUser ID: {html.code(f"{userid}")}\n\nPress following button to grant permission"
        await callback.message.edit_text(res, reply_markup=grant_perm_to(userid, mention))
    else:
        await callback.message.edit_text("Message is not replied to any user's message", reply_markup=types.ReplyKeyboardRemove())
        sleep(3)
        await callback.message.delete()

@allow.callback_query(CbDataStartsWith("grant_"))
async def grant_perm(callback: types.CallbackQuery):
    userid = int(callback.data.split("_")[1])
    mention = callback.data.split("_")[2]
    # db.execute("INSERT INTO user (userid, perm) VALUES (?, 1)", (userid,))
    await callback.message.edit_text(f"Congratulations, {mention}! You have been given permission to use the bot.", reply_markup=goto_bot)
    # sleep(3)
    # await callback.message.delete()

@allow.callback_query(CbData("cancel_perm"))
async def cancel_fetch(callback: types.CallbackQuery):
    await callback.message.edit_text("Operation cancelled", reply_markup=types.ReplyKeyboardRemove())
    sleep(3)
    await callback.message.delete()