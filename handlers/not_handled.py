from aiogram import Router
from aiogram.types import Message, CallbackQuery
from keyboards.inline import main_menu_in
from filters import IsFromInlineMessageCallback, IsPrivate, IsPrivateCallback

remover = Router()
remover.message.filter(IsPrivate())
remover.callback_query.filter(IsPrivateCallback())

@remover.message()
async def remove(message: Message) -> None:
    await message.reply("Not recognized", reply_markup=main_menu_in)
    # print(f"Not handled message: {message}")


@remover.callback_query(IsFromInlineMessageCallback())
async def not_for_you(callback: CallbackQuery) -> None:
    await callback.answer("Callback not for you")

@remover.callback_query()
async def remove_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Not recognized", reply_markup=main_menu_in)
    await callback.answer("Not recognized")