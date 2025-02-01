from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

class CbData(BaseFilter):
    def __init__(self, data: str):
        self.exp_data = data
    async def __call__(self, callback: CallbackQuery) -> bool:
        return self.exp_data == callback.data

class CbDataStartsWith(BaseFilter):
    def __init__(self, data: str):
        self.exp_data = data
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.startswith(self.exp_data)