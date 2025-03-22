from aiogram import Router
from aiogram.types import Message, CallbackQuery
from keyboards.inline import main_menu_in
from filters import IsFromInlineMessageCallback, IsPrivate, IsPrivateCallback
import asyncio

remover = Router()
remover.message.filter(IsPrivate())
remover.callback_query.filter(IsPrivateCallback())

@remover.message()
async def remove(message: Message) -> None:
    response = await message.reply("Not recognized", reply_markup=main_menu_in)
    # Delete the message after 5 seconds
    await asyncio.sleep(5)
    await response.delete()


@remover.callback_query(IsFromInlineMessageCallback())
async def not_for_you(callback: CallbackQuery) -> None:
    await callback.answer("Callback not for you")

@remover.callback_query()
async def remove_callback(callback: CallbackQuery) -> None:
    print(f"Callback not recognized: {callback.data}")
    response = await callback.message.answer("Not recognized", reply_markup=main_menu_in)
    await callback.answer("Not recognized")
    # Delete the message after 5 seconds
    await asyncio.sleep(5)
    await response.delete()