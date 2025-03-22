from aiogram import Router
from aiogram.types import Message, CallbackQuery
from keyboards.inline import usr_main_inl_key
from filters import IsFromInlineMessageCallback, IsPrivate, IsPrivateCallback, IsUser, IsUserCallback
import asyncio

usrem = Router()
usrem.message.filter(IsPrivate(), IsUser())
usrem.callback_query.filter(IsPrivateCallback(), IsUserCallback())

@usrem.message()
async def remove(message: Message) -> None:
    response = await message.reply("Sizni tushunmadim.", reply_markup=usr_main_inl_key)
    # Delete the message after 5 seconds
    await asyncio.sleep(5)
    await response.delete()


@usrem.callback_query(IsFromInlineMessageCallback())
async def not_for_you(callback: CallbackQuery) -> None:
    await callback.answer("Bu tugma siz uchun emas")

@usrem.callback_query()
async def remove_callback(callback: CallbackQuery) -> None:
    print(f"Callback not recognized: {callback.data}")
    response = await callback.message.answer("Sizni tushunmadim.", reply_markup=usr_main_inl_key)
    await callback.answer("Yuklanmoqda...")
    # Delete the message after 5 seconds
    await asyncio.sleep(5)
    await response.delete()