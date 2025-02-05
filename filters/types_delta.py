from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsTextMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'text'

class IsPhotoMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'photo'

class IsVideoMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'video'

class IsDocumentMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'document'

class IsAudioMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'audio'

class IsVoiceMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'voice'

class IsStickerMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.content_type == 'sticker'
