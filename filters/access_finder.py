from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, InlineQuery
from data import config
from loader import db, bot
from utils.chat_info import checksub

class IsRegistered(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return db.fetchone("SELECT idx FROM users WHERE userid=%s::text", (message.from_user.id,)) != None

class IsNotRegistered(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # print(db.fetchone("SELECT idx FROM users WHERE userid=%s", (message.from_user.id,)))
        return db.fetchone("SELECT idx FROM users WHERE userid=%s::text", (message.from_user.id,)) == None

class IsSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        allowed = int(db.fetchall("SELECT allowed FROM users WHERE userid=%s::text", (message.from_user.id,))[0])
        return bool(allowed)

class IsNotSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        allowed = int(db.fetchall("SELECT allowed FROM users WHERE userid=%s::text", (message.from_user.id,))[0])
        return not bool(allowed)

class IsSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = int(db.fetchall("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))[0])
        return bool(allowed)

class IsNotSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = int(db.fetchall("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))[0])
        return not bool(allowed)

class IsAdmin(BaseFilter):
    # def __init__(self, args):
    #     print(args)
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMINS and message.chat.type == "private"
    
class IsAdminCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in config.ADMINS and not callback.inline_message_id or callback.message.chat.type == "private"

class IsAdminInline(BaseFilter):
    async def __call__(self, inline: InlineQuery) -> bool:
        return inline.from_user.id in config.ADMINS and inline.chat_type == "private"

class IsUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        res = message.from_user.id not in config.ADMINS
        return res and message.chat.type == "private"

class IsUserCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        res = callback.from_user.id not in config.ADMINS
        return res and not callback.inline_message_id or callback.message.chat.type == "private"

class IsPrivateCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.message.chat.type == "private"

class IsNotPrivateCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.message.chat.type != "private"

class IsFromInlineMessageCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.inline_message_id != None

class IsNotFromInlineMessageCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.inline_message_id == None