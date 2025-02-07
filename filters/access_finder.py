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
        channels = db.fetchall("SELECT chid FROM channel WHERE NOT post = 1")
        
        for ch in channels:
            if not await checksub(message.from_user.id, ch[0]):
            #  member = await bot.get_chat_member(chat_id=ch[0], user_id=message.from_user.id)
            # print(member)
            # if member.status not in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        return True

class IsNotSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        channels = db.fetchall("SELECT chid FROM channel WHERE NOT post = 1")
        print(channels)
        for ch in channels:
            if not await checksub(message.from_user.id, ch[0]):
            # member = await bot.get_chat_member(chat_id=ch[0], user_id=message.from_user.id)
            # print(member)
            # if member.status not in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return True
        return False

class IsSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        channels = db.fetchall("SELECT chid FROM channel WHERE NOT post = 1")
        for ch in channels:
            if not await checksub(callback.from_user.id, ch[0]):
            # member = await bot.get_chat_member(chat_id=ch[0], user_id=callback.from_user.id)
            # print(member)
            # if member.status not in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            # if callback.from_user.id not in getsubs(ch[0]):
                return False
        return True

class IsNotSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        channels = db.fetchall("SELECT chid FROM channel WHERE NOT post = 1")
        for ch in channels:
            if not await checksub(callback.from_user.id, ch[0]):
            # if callback.from_user.id in getsubs(ch[0]):
                return True
        return False

class IsAdmin(BaseFilter):
    # def __init__(self, args):
    #     print(args)
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMINS and message.chat.type == "private"
    
class IsAdminCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in config.ADMINS #and callback.message.chat.type == "private"

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
        return res and callback.message.chat.type == "private"