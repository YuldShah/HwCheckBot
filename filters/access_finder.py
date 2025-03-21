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
        
        # Manual permission (allowed=2) overrides channel subscription requirements
        if allowed and allowed[0] == 2:
            return True
            
        # If admin explicitly denied access (allowed=-1), always return False
        if allowed and allowed[0] == -1:
            return False
        
        # If user has standard permission (allowed=1), check they're still subscribed
        if allowed and allowed[0] == 1:
            # Check if they're still subscribed to all required channels
            channels = db.fetchall("SELECT chid FROM channel")
            if channels:
                for channel in channels:
                    if await checksub(message.from_user.id, channel[0]):
                        return True
            return False
        
        # Otherwise check channel subscriptions
        channels = db.fetchall("SELECT chid FROM channel")
        if not channels:
            return True
        
        # Check if user is subscribed to ALL required channels
        for channel in channels:
            if await checksub(message.from_user.id, channel[0]):
                return True
        
        # User is subscribed to all channels - update database
        db.query("UPDATE users SET allowed=0 WHERE userid=%s::text", (message.from_user.id,))
        return False

class IsNotSubscriber(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (message.from_user.id,))
        
        # Manual permission (allowed=2) overrides channel subscription requirements
        if allowed and allowed[0] == 2:
            return False
            
        # If admin explicitly denied access (allowed=-1), always return True 
        if allowed and allowed[0] == -1:
            return True
            
        # If user has standard permission (allowed=1), check they're still subscribed
        if allowed and allowed[0] == 1:
            # Check if they're still subscribed to all required channels
            channels = db.fetchall("SELECT chid FROM channel")
            if channels:
                for channel in channels:
                    if await checksub(message.from_user.id, channel[0]):
                        return False
            return True
            
        # Otherwise check channel subscriptions
        channels = db.fetchall("SELECT chid FROM channel")
        if not channels:
            return False
        
        # Check if user is missing ANY required channel
        for channel in channels:
            if await checksub(message.from_user.id, channel[0]):
                return False
                
        # User is subscribed to all channels - update database
        db.query("UPDATE users SET allowed=0 WHERE userid=%s::text", (message.from_user.id,))
        return True

class IsSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
        
        # Manual permission (allowed=2) overrides channel subscription requirements
        if allowed and allowed[0] == 2:
            return True
            
        # If admin explicitly denied access (allowed=-1), always return False
        if allowed and allowed[0] == -1:
            return False
            
        # If user has standard permission (allowed=1), check they're still subscribed
        if allowed and allowed[0] == 1:
            # Check if they're still subscribed to all required channels
            channels = db.fetchall("SELECT chid FROM channel")
            if channels:
                for channel in channels:
                    if await checksub(callback.from_user.id, channel[0]):
                        return True
            return False
            
        # Otherwise check channel subscriptions
        channels = db.fetchall("SELECT chid FROM channel")
        if not channels:
            return True
        
        # Check if user is subscribed to ALL required channels
        for channel in channels:
            if await checksub(callback.from_user.id, channel[0]):
                return True
                
        # User is subscribed to all channels - update database
        db.query("UPDATE users SET allowed=0 WHERE userid=%s::text", (callback.from_user.id,))
        return False

class IsNotSubscriberCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        allowed = db.fetchone("SELECT allowed FROM users WHERE userid=%s::text", (callback.from_user.id,))
        
        # Manual permission (allowed=2) overrides channel subscription requirements
        if allowed and allowed[0] == 2:
            return False
            
        # If admin explicitly denied access (allowed=-1), always return True
        if allowed and allowed[0] == -1:
            return True
            
        # If user has standard permission (allowed=1), check they're still subscribed
        if allowed and allowed[0] == 1:
            # Check if they're still subscribed to all required channels
            channels = db.fetchall("SELECT chid FROM channel")
            if channels:
                for channel in channels:
                    if await checksub(callback.from_user.id, channel[0]):
                        return False
            db.query("UPDATE users SET allowed=0 WHERE userid=%s::text", (callback.from_user.id,))
            return True
            
        # Otherwise check channel subscriptions
        channels = db.fetchall("SELECT chid FROM channel")
        if not channels:
            return False
        
        # Check if user is missing ANY required channel
        for channel in channels:
            if await checksub(callback.from_user.id, channel[0]):
                return False
                
        # User is subscribed to all channels - update database
        db.query("UPDATE users SET allowed=0 WHERE userid=%s::text", (callback.from_user.id,))
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

class IsArchiveAllowed(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return db.fetchone("SELECT arch FROM users WHERE userid=%s::text", (message.from_user.id,))[0] == 1

class IsNotArchiveAllowed(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return db.fetchone("SELECT arch FROM users WHERE userid=%s::text", (message.from_user.id,))[0] == 0

class IsArchiveAllowedCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return db.fetchone("SELECT arch FROM users WHERE userid=%s::text", (callback.from_user.id,))[0] == 1

class IsNotArchiveAllowedCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return db.fetchone("SELECT arch FROM users WHERE userid=%s::text", (callback.from_user.id,))[0] == 0

class IsPrivate(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"

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