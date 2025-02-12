import re
from aiogram import Router, types, F
from data import dict, config
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from states import sets
from keyboards.inline import post_chan, set_menu, mandconfirm, ping_set, back_inl_key
from keyboards.regular import main_key, back_key
from aiogram.fsm.context import FSMContext
from loader import db, bot
from time import sleep, monotonic
from aiogram import html

set = Router()

set.message.filter(IsAdmin())
set.callback_query.filter(IsAdminCallback())
# bot.send_message(config.ADMINS[0], "Settings handler loaded", reply_parameters=)

@set.message(F.text == dict.settings)
async def sett(message: types.Message, state: FSMContext):
    await state.set_state(sets.smenu)
    await message.answer(f"Menu: <b>{dict.settings}</b>", reply_markup=main_key)
    response = "Here you can change some configuration settings, check the ping with the Telegram servers"
    await message.answer(response, reply_markup=set_menu)

@set.callback_query(CbData("ping"), sets.smenu)
async def ping(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(sets.ping)
    start_time = monotonic()
    sent_message = await callback.message.edit_text("Pinging... 🏓", reply_markup=back_inl_key)
    end_time = monotonic()
    
    ping_ms = (end_time - start_time) * 1000  # Convert to milliseconds
    await sent_message.edit_text(f"Pong! 🏓\n\nPing: {html.code(f"{ping_ms:.2f} ms")}", reply_markup=ping_set)
    await callback.answer("Pinged!")

@set.callback_query(CbData("refresh_ping"), sets.ping)
async def refresh_ping(callback: types.CallbackQuery, state: FSMContext) -> None:
    start_time = monotonic()
    sent_message = await callback.message.edit_text("Pinging... 🏓", reply_markup=back_inl_key)
    end_time = monotonic()
    
    ping_ms = (end_time - start_time) * 1000  # Convert to milliseconds
    await sent_message.edit_text(f"Pong! 🏓\n\nPing: {html.code(f"{ping_ms:.2f} ms")}", reply_markup=ping_set)
    await callback.answer("Pinged!")

@set.callback_query(CbData("back"), sets.ping)
async def back_to_s(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(sets.smenu)
    await callback.message.edit_text("Here you can change some configuration settings, check the ping with the Telegram servers", reply_markup=set_menu)
    await callback.answer("Back to settings menu")

@set.callback_query(CbData("defaults"), sets.smenu)
async def defaults(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Here you will be able to change the defaule number of options for multiple choice questions, and the default number of questions that will be shown in a page and etc.", reply_markup=back_inl_key)
    await state.set_state(sets.defs)

@set.callback_query(CbData("back"), sets.defs)
async def back_to_s(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(sets.smenu)
    await callback.message.edit_text("Here you can change some configuration settings, check the ping with the Telegram servers", reply_markup=set_menu)
    await callback.answer("Back to settings menu")