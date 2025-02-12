from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, InlineQuery
from data import config
from loader import db, bot
from utils.chat_info import checksub
from utils.yau import checksub

class IsRegistered(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return db.fetchone("SELECT idx FROM users WHERE userid=%s::text", (message.from_user.id,)) != None

class IsNotRegistered(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # print(db.fetchone("SELECT idx FROM users WHERE userid=%s", (message.from_user.id,)))
        return db.fetchone("SELECT idx FROM users WHERE userid=%s::text", (message.from_user.id,)) == None

class IsSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (message.from_user.id,))
        if allowed:
            return bool(int(allowed[0]))
        chid = db.fetchone("SELECT chid FROM channel")
        if chid:
            chid = int(chid[0])
            return await checksub(message.from_user.id, chid)
        return False

class IsNotSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (message.from_user.id,))
        if allowed:
            return not bool(int(allowed[0]))
        chid = db.fetchone("SELECT chid FROM channel")
        if chid:
            chid = int(chid[0])
            return not await checksub(message.from_user.id, chid)
        return True

class IsSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
        if allowed:
            return bool(int(allowed[0]))
        chid = db.fetchone("SELECT chid FROM channel")
        if chid:
            chid = int(chid[0])
            return await checksub(callback.from_user.id, chid)
        return False

class IsNotSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
        if allowed:
            return not bool(int(allowed[0]))
        chid = db.fetchone("SELECT chid FROM channel")
        if chid:
            chid = int(chid[0])
            return not await checksub(callback.from_user.id, chid)
        return True

class IsAdmin(BaseFilter):
    # def __init__(self, args):
    #     print(args)
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMINS and message.chat.type == "private"
    
class IsAdminCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in config.ADMINS and (callback.inline_message_id is not None or (callback.inline_message_id is None and callback.message and callback.message.chat.type == "private")) # Not inline and private"

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
        return res and (callback.inline_message_id is not None or (callback.inline_message_id is None and callback.message and callback.message.chat.type == "private"))

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