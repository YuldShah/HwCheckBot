from aiogram import types, Router, F, html
from data import config
from keyboards.inline import perm_inl
from filters import InlineData, InlineDataStartsWith, IsAdmin, IsAdminCallback

allow = Router()

allow.message.filter(IsAdmin())
allow.callback_query.filter(IsAdminCallback())
allow.inline_query.filter()

@allow.inline_query(InlineData("allow"))
async def allow_inline(inline: types.InlineQuery):
    res = types.InlineQueryResultArticle(
        title="Allow",
        description="Allow new user to use the bot",
        input_message_content=types.InputTextMessageContent(
            message_text="Allow new user to use the bot"
        ),
        reply_markup=perm_inl(inline.from_user.first_name, inline.from_user.id)
    )
    await inline.answer([res], cache_time=1, is_personal=True)