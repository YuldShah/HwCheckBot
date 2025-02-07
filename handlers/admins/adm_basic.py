import time
from aiogram import Router, types, F, html
from aiogram.filters import Command, CommandStart
from filters import IsAdmin, IsAdminCallback, CbData, IsStickerMessage
from aiogram.fsm.context import FSMContext
from data import dict
from loader import db, bot
from keyboards.inline import mandchans
from keyboards.regular import adm_default, main_key
# from states import mands

admin = Router()

admin.message.filter(IsAdmin())
admin.callback_query.filter(IsAdminCallback())

@admin.message(F.text == dict.main_menu)
@admin.message(CommandStart())
async def adminstart(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    # await bot.get_chat(message.from_user.id)
    await message.answer_sticker("CAACAgIAAxkBAANHZ6OBeJYZztktbr8YZHZ3muuKlr0AAqYCAAJWnb0K5jqXX4k9st02BA")
    await message.answer(f"👋 Hi, {html.bold(message.from_user.mention_html())}\n\n👀 You're an admin, do whatever you want!", reply_markup=adm_default)


@admin.callback_query(CbData("main_menu"))
async def adminmenu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Bosh menyuga qaytingiz", reply_markup=adm_default)
    await callback.message.delete()

@admin.message(IsStickerMessage())
async def ret_sticker_id(message: types.Message, state: FSMContext) -> None:
    await message.reply(f"Sticker id {html.code(message.sticker.file_id)}")

# @admin.message(F.text == dict.mands)
# async def pmands(message: types.Message, state: FSMContext) -> None:
#     await state.set_state(mands.mmenu)
#     await message.answer(f"Menyu: <b>{dict.mands}</b>", reply_markup=main_key)
#     response = "Hozircha majburiy chatlar mavjud emas. Ularni shu yerdan qo'sha olasiz:"
#     channels = db.fetchall("SELECT title, link, idx FROM channel WHERE NOT post = 1")
#     if channels:
#         response = "Following are the mandatory chats to join. You can add new or delete existing ones."
#     await message.answer(response, reply_markup=mandchans(channels))