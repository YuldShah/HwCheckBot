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
    response = "Here you can change some configuration settings and manage permission giving chat"
    await message.answer(response, reply_markup=set_menu)

@set.callback_query(CbData("post"), sets.smenu)
async def post_c(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(sets.post)
    response = "Here you can change or reset the permission giving chat"
    channel = db.fetchone("SELECT title, link FROM channel WHERE post > 0")
    print(channel)
    if not channel:
        response = "The chat that users will be checked to give permission to the bot was not set, you can set a new one"
    await callback.message.edit_text(response, reply_markup=post_chan(channel))

@set.callback_query(CbData("back"), sets.post)
async def back_to_s(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(sets.smenu)
    # await callback.message.answer(f"Menu: <b>{dict.settings}</b>", reply_markup=main_key)
    response = "Here you can change some configuration settings and manage permission giving chat"
    await callback.message.edit_text(response, reply_markup=set_menu)
    await callback.answer("Back to settings menu")

@set.callback_query(CbData("set_new"), sets.post)
async def setnew(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(sets.link)
    await callback.message.answer("Forward a message from the private chat to here", reply_markup=back_key)
    await callback.message.delete()

@set.message(F.text == dict.back, sets.link)
async def back_to_c(message: types.Message, state: FSMContext):
    await state.set_state(sets.post)
    await message.answer("Back to posting channel menu", reply_markup=main_key)
    response = "Here you can change or reset the permission giving chat"
    channel = db.fetchone("SELECT title, link FROM channel WHERE post > 0")
    if not channel:
        response = "Posting channel was not set, you can set it in two ways"
    await message.answer(response, reply_markup=post_chan(channel))

@set.message(sets.link)
async def get_link(message: types.Message, state: FSMContext):
    # USERNAME_PATTERN = r"^[a-zA-Z][\w\d_]{4,31}$"  # Username (e.g., channelname)
    # AT_USERNAME_PATTERN = r"^@[a-zA-Z][\w\d_]{4,31}$"  # Username starting with @
    # PRIVATE_LINK_PATTERN = r"^https://t\.me/\+\w+$"  # Private links (e.g., https://t.me/+W3UbzATqipEzYTVi)
    # PUBLIC_LINK_PATTERN = r"^https://t\.me/[a-zA-Z][\w\d_]{4,31}$"  # Public links (e.g., https://t.me/channelname)
    # text = None
    lk = None
    chanid = None
    # print(message.forward_from_chat)
    if message.forward_from_chat:
        chanid = message.forward_from_chat.id
        if message.forward_from_chat.username == None:
            try:
                lk = (await bot.create_chat_invite_link(chat_id=chanid, name=f"Join link by {config.bot_info.username}")).invite_link
            except Exception as e:
                print(e)
                await message.answer("Please, make sure to add the bot to the chat as an admin and try again")
                return
        else:
            lk = f"https://t.me/{message.forward_from_chat.username}"
    else:
        await message.answer("This message isn't forwarded from any chat. Forward a message from the private chat to here")
        # data = await state.get_data()
    try:
        channel_info = await bot.get_chat(chanid)
        mb_cnt = await bot.get_chat_member_count(chanid)
        mebot = await bot.get_chat_member(chat_id=chanid, user_id=config.bot_info.id)
    except Exception as e:
        print(e)
        print(lk)
        await message.answer("Please, make sure to add the bot to the chat as an admin, chat exists and try again")
        return
    # print(title, lk)
    title = channel_info.title
    
    await state.set_state(sets.confirm)
    await state.update_data(title=title)
    await state.update_data(link=lk)
    await state.update_data(chid=chanid)
    # print(title, lk)
    await message.answer(f"Check and confirm everything is correct\n\nChat Information:"
            f"\n\t\tTitle: {html.bold(channel_info.title)}"
            f"\n\t\tMembers count: {html.bold(mb_cnt)}"
            f"\n\t\tDescription: {html.blockquote(channel_info.description or 'No description')}", reply_markup=mandconfirm((title, lk)), disable_web_page_preview=True)

@set.message(F.text == dict.back, sets.confirm)
async def back_to_link(message: types.Message, state: FSMContext) -> None:
    await state.set_state(sets.link)
    await message.answer("Now send the right link", reply_markup=back_key)

@set.callback_query(CbData("reset"), sets.post)
async def reset(callback: types.CallbackQuery, state: FSMContext) -> None:
    old = db.fetchone("SELECT title, link, chid, post FROM channel WHERE post > 0")
    if old and old[3]==1:
        db.query("DELETE FROM channel WHERE chid = %s", (old[2],))
    else:
        db.query("UPDATE channel SET post = 0 WHERE chid = %s", (old[2],))
    await callback.answer("Reset successfull")
    await post_c(callback, state)

@set.callback_query(sets.confirm)
async def confirm(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data == "cancel":
        await callback.answer("Cancelled")
        await callback.message.answer("Back to posting channel menu", reply_markup=main_key)
        await post_c(callback, state)
        # await callback.message.delete()
        return
    data = await state.get_data()
    chid = data.get("chid")
    title = data.get("title")
    link = data.get("link")
    chck = db.fetchone("SELECT title FROM channel WHERE chid = %s AND post > 0", (chid,))
    if chck:
        msg = await callback.message.answer(f"This channel already has been set as the posting channel")
        await callback.answer("Already posting channel")
        await callback.message.answer("Back to posting channel menu", reply_markup=main_key)
        await post_c(callback, state)
        sleep(2)
        await msg.delete()
        # await callback.message.delete()
        return
    # channel_info = await bot.get_chat(link)
    old = db.fetchone("SELECT title, link, chid, post FROM channel WHERE post > 0")
    print(old)
    if old:
        if old[3]==1:
            db.query("DELETE FROM channel WHERE chid = %s", (old[2],))
        else:
            db.query("UPDATE channel SET post = 0 WHERE chid = %s", (old[2],))
    sme = db.fetchone("SELECT post FROM channel WHERE chid = %s", (chid,))
    print(sme)
    if sme:
        print("Updating")
        db.query("UPDATE channel SET post = 2 WHERE chid = %s", (chid,))
    else:
        db.query("INSERT INTO channel (chid, title, link, post) VALUES (%s, %s, %s, 1)", (chid, title, link))
    await callback.answer(f"Successfully set")
    await callback.message.answer("Back to posting channel menu", reply_markup=main_key)
    await post_c(callback, state)
    # await callback.message.delete()

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
    await callback.message.edit_text("Here you can change some configuration settings and manage permission giving chat", reply_markup=set_menu)
    await callback.answer("Back to settings menu")
