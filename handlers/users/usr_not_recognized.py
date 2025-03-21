from aiogram import Router
from aiogram.types import Message, CallbackQuery
from keyboards.inline import usr_main_inl_key
from filters import IsFromInlineMessageCallback, IsPrivate, IsPrivateCallback, IsUser, IsUserCallback

usrem = Router()
usrem.message.filter(IsPrivate(), IsUser())
usrem.callback_query.filter(IsPrivateCallback(), IsUserCallback())

@usrem.message()
async def remove(message: Message) -> None:
    await message.reply("Sizni tushunmadim.", reply_markup=usr_main_inl_key)
    # print(f"Not handled message: {message}")


@usrem.callback_query(IsFromInlineMessageCallback())
async def not_for_you(callback: CallbackQuery) -> None:
    await callback.answer("Bu tugma siz uchun emas")

@usrem.callback_query()
async def remove_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Sizni tushunmadim.", reply_markup=usr_main_inl_key)
    await callback.answer("Yuklanmoqda...")