from aiogram import types, Router, F, html
from data import config
from keyboards.inline import perm_inl
# import hashlib
from time import sleep
from filters import InlineData, InlineDataStartsWith, IsAdmin, IsAdminCallback, IsAdminInline, CbData, CbDataStartsWith

allow = Router()

allow.message.filter(IsAdmin())
allow.callback_query.filter(IsAdminCallback())
allow.inline_query.filter(IsAdminInline())



@allow.inline_query(InlineData("allow"))
async def allow_inline(inline: types.InlineQuery):
    print("allow")
    # unique_id = hashlib.md5(str(inline.from_user.id).encode()).hexdigest()
    res = types.InlineQueryResultArticle(
        id="wtf",
        title="Granting permission",
        description="Grant permission to user",
        input_message_content=types.InputTextMessageContent(
            message_text="Botga ruxsat olish uchun quyidagi tugmani bosing."
        ),
        reply_markup=perm_inl
    )
    await inline.answer([res], cache_time=1, is_personal=True)

@allow.inline_query()
async def default_inline(inline: types.InlineQuery):
    print("inline")
    res = [
        types.InlineQueryResultArticle(
            id = "1",
            title = "allow",
            description = "Used to permission to user",
            input_message_content = types.InputTextMessageContent(message_text=f"Wrong query! You should have entered {html.code(f"@{config.bot_info.username} allow")} and press the resultant button.")
        ),
        types.InlineQueryResultArticle(
            id = "2",
            title = "remove",
            description = "Used to remove access from user",
            input_message_content = types.InputTextMessageContent(message_text=f"Wrong query! You should have entered {html.code(f"@{config.bot_info.username} remove")} and press the resultant button.")
        )
    ]
    await inline.answer(res, cache_time=1, is_personal=True)


# @allow.callback_query(CbData("fetch_data"))
# async def fetch_data(callback: types.CallbackQuery):
#     msg = await callback.bot.edit_message_text(text="Fetching data", inline_message_id=callback.inline_message_id)
#     if not msg.reply_to_message:
#         await callback.answer("No message found from inline message")
#         return
#     else:
#         await msg.edit_text(f"Data fetched\n\nUser: {html.bold(f"{msg.reply_to_message.from_user.mention_html()}\nUser ID: {msg.reply_to_message.from_user.id}")}")
#         return
#     await callback.inline_message_id
#     if not callback.message:
#         await callback.answer("No message found")
#         return
#     if callback.message.reply_to_message:
#         userid = callback.message.reply_to_message.from_user.id
#         mention = callback.message.reply_to_message.from_user.mention_html()
#         res = f"User: {html.bold(f"{mention}")}\nUser ID: {html.code(f"{userid}")}\n\nPress following button to grant permission"
#         await callback.message.edit_text(res, reply_markup=grant_perm_to(userid, mention))
#     else:
#         await callback.message.edit_text("Message is not replied to any user's message", reply_markup=types.ReplyKeyboardRemove())
#         sleep(3)
#         await callback.message.delete()

# @allow.callback_query(CbDataStartsWith("grant_"))
# async def grant_perm(callback: types.CallbackQuery):
#     userid = int(callback.data.split("_")[1])
#     mention = callback.data.split("_")[2]
#     # db.execute("INSERT INTO user (userid, perm) VALUES (?, 1)", (userid,))
#     await callback.message.edit_text(f"Congratulations, {mention}! You have been given permission to use the bot.", reply_markup=goto_bot(config.bot_info.username))
#     # sleep(3)
#     # await callback.message.delete()

# @allow.callback_query(CbData("cancel_perm"))
# async def cancel_fetch(callback: types.CallbackQuery):
#     await callback.message.edit_text("Operation cancelled", reply_markup=types.ReplyKeyboardRemove())
#     sleep(3)
#     await callback.message.delete()