import re
import asyncio
from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, mandconfirm, man_access
from keyboards.inline.comm_inline import confirm_inl_key
from keyboards.regular import main_key, back_key
from time import sleep
from states import accstates
from aiogram.fsm.context import FSMContext
from filters import IsAdmin, IsAdminCallback
from loader import bot, db

access = Router()

access.message.filter(IsAdmin())
access.callback_query.filter(IsAdminCallback())


@access.message(F.text == dict.man_access)
async def manage_access(message: types.Message, state: FSMContext):
    await state.set_state(accstates.acmenu)
    await message.answer(f"Menu: <b>{dict.man_access}</b>", reply_markup=main_key)
    response = "Here you can manage the access of users to the bot"
    await message.answer(response, reply_markup=access_menu)

@access.callback_query(F.data == "post", accstates.acmenu)
async def post_c(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.edit_text(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "back", accstates.post)
async def back_to_s(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.acmenu)
    response = "Here you can manage the access of users to the bot"
    await callback.message.edit_text(response, reply_markup=access_menu)
    await callback.answer(f"Back to {dict.man_access} menu")

# @access.callback_query(F.data == "add_perm_chat", accstates.post)
# async def add_perm_chat(callback: types.CallbackQuery, state: FSMContext):
#     await state.set_state(accstates.link)
#     await callback.message.answer("Send the title of the chat to add", reply_markup=back_key)
#     await callback.message.delete()

# @access.message(accstates.link, F.text == dict.back)


@access.callback_query(F.data == "add_perm_chat", accstates.post)
async def get_title(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.chat_link)
    await callback.message.answer("Forward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id", reply_markup=back_key)
    await callback.message.delete()

@access.message(accstates.chat_link, F.text == dict.back)
async def back_to_c(message: types.Message, state: FSMContext):
    await state.set_state(accstates.post)
    await message.answer("Back to posting channel menu", reply_markup=main_key)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await message.answer(response, reply_markup=post_chan(channels))

@access.message(accstates.chat_link)
async def get_link(message: types.Message, state: FSMContext):
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
        # chatid = None
        print(message.text)
        if message.text[1:].isnumeric() and message.text.startswith("-100"):
            chanid = message.text
        else:
            await message.answer("This message neither forwarded from private chat nor includes a valid chat id. Forward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id")
            return
        # data = await state.get_data()
    try:
        channel_info = await bot.get_chat(chanid)
        mb_cnt = await bot.get_chat_member_count(chanid)
        lk = (await bot.create_chat_invite_link(chat_id=chanid, name=f"Join link by {config.bot_info.username}")).invite_link
            # except Exception as e:
            #     print(e)
            #     await message.answer("Please, make sure to add the bot to the chat as an admin and try again")
            #     return
        # mebot = await bot.get_chat_member(chat_id=chanid, user_id=config.bot_info.id)
    except Exception as e:
        print(e)
        print(lk)
        await message.answer("Please, make sure to add the bot to the chat as an admin, chat exists and try again")
        return
    title = channel_info.title
    print(title, lk)
    print(channel_info)


    
    await state.set_state(accstates.confirm)
    await state.update_data(title=title)
    await state.update_data(link=lk)
    await state.update_data(chid=chanid)
    # print(title, lk)
    await message.answer(f"Check and confirm everything is correct\n\nChat Information:"
            f"\n\t\tTitle: {html.bold(channel_info.title)}"
            f"\n\t\tMembers count: {html.bold(mb_cnt)}"
            f"\n\t\tDescription: {html.blockquote(channel_info.description or 'No description')}", reply_markup=mandconfirm((title, lk)), disable_web_page_preview=True)

@access.message(F.text == dict.back, accstates.confirm)
async def back_to_chat_link(message: types.Message, state: FSMContext) -> None:
    await state.set_state(accstates.chat_link)
    # await state.set_state(accstates.link)
    await message.answer("Forward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id", reply_markup=back_key)

@access.message(F.text == dict.back, accstates.link)
async def back_to_c(message: types.Message, state: FSMContext):
    await state.set_state(accstates.post)
    await message.answer("Back to posting channel menu", reply_markup=main_key)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await message.answer(response, reply_markup=post_chan(channels))

@access.message(accstates.link)
async def get_link(message: types.Message, state: FSMContext):
    lk = None
    chanid = None
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
        if message.text[1:].isnumeric() and message.text.startswith("-100"):
            chanid = message.text
        else:
            await message.answer("This message neither forwarded from private chat nor includes a valid chat id. Forward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id")
            return
    try:
        channel_info = await bot.get_chat(chanid)
        mb_cnt = await bot.get_chat_member_count(chanid)
        if channel_info.username:
            lk = f"https://t.me/{channel_info.username}"
        else:
            lk = (await bot.create_chat_invite_link(chat_id=chanid, name=f"Join link by {config.bot_info.username}")).invite_link
    except Exception as e:
        print(e)
        print(lk)
        await message.answer("Please, make sure to add the bot to the chat as an admin, chat exists and try again")
        return
    title = channel_info.title
    print(title, lk)
    print(channel_info)
    await state.set_state(accstates.confirm)
    await state.update_data(title=title)
    await state.update_data(link=lk)
    await state.update_data(chid=chanid)
    await message.answer(f"Check and confirm everything is correct\n\nChat Information:"
            f"\n\t\tTitle: {html.bold(channel_info.title)}"
            f"\n\t\tMembers count: {html.bold(mb_cnt)}"
            f"\n\t\tDescription: {html.blockquote(channel_info.description or 'No description')}", reply_markup=confirm_inl_key, disable_web_page_preview=True)

@access.callback_query(F.data == "reset", accstates.post)
async def reset_confirm(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(accstates.reset_con)
    await state.update_data(action="reset_all")
    message_text = "⚠️ Are you sure you want to delete ALL permission chats?\nThis action cannot be undone."
    await callback.message.edit_text(message_text, reply_markup=confirm_inl_key)

@access.callback_query(F.data.startswith("delete_perm_"))
async def delete_perm_chat_confirm(callback: types.CallbackQuery, state: FSMContext) -> None:
    idx = callback.data.split("_")[2]
    channel = db.fetchone("SELECT title, link, idx FROM channel WHERE idx=%s", (idx,))
    if not channel:
        await callback.answer("Channel not found")
        return
    await state.set_state(accstates.del_con)
    await state.update_data(action="delete_chat", chat_idx=idx)
    message_text = f"⚠️ Are you sure you want to delete the chat '{html.bold(channel[0])}'?\nThis action cannot be undone."
    await callback.message.edit_text(message_text, reply_markup=mandconfirm((channel[0], channel[1])), disable_web_page_preview=True)

@access.callback_query(F.data == "confirm", accstates.reset_con)
async def confirm_reset_all(callback: types.CallbackQuery, state: FSMContext) -> None:
    db.query("DELETE FROM channel")
    await callback.answer("All permission chats have been deleted")
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.edit_text(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "cancel", accstates.reset_con)
async def cancel_reset_all(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Operation cancelled")
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.edit_text(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "confirm", accstates.del_con)
async def confirm_delete_chat(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    idx = data.get("chat_idx")
    db.query("DELETE FROM channel WHERE idx=%s", (idx,))
    await callback.answer(f"Chat has been deleted")
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.edit_text(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "cancel", accstates.del_con)
async def cancel_delete_chat(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Operation cancelled")
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.edit_text(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "manually")
async def manually(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(accstates.manl)
    await callback.message.edit_text("You can give or remove access to users manually here", reply_markup=man_access)

@access.callback_query(F.data == "back", accstates.manl)
async def back_to_m(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(f"Back to {html.bold(f"{dict.man_access}")} menu", reply_markup=main_key)
    await state.set_state(accstates.acmenu)
    await callback.message.answer(f"Here you can manage the access of users to the bot", reply_markup=access_menu)
    await callback.message.delete()

@access.callback_query(F.data == "add_access")
async def add_access_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(accstates.adda)
    await callback.message.answer("Forward the message of the user you want to give access to the bot, or give the id of the user.", reply_markup=back_key)
    await callback.message.delete()

@access.message(F.text == dict.back, accstates.adda)
async def back_to_a(message: types.Message, state: FSMContext) -> None:
    await message.answer("Back to the access menu.", reply_markup=main_key)
    await state.set_state(accstates.manl)
    await message.answer("You can give or remove access to users manually here", reply_markup=man_access)

@access.message(accstates.adda)
async def add_access(message: types.Message, state: FSMContext) -> None:
    if message.forward_from:
        userid = message.forward_from.id
        username = message.forward_from.username
        mention = message.forward_from.mention_html()
    elif message.text.isnumeric():
        userid = int(message.text)
        mention = f"<a href='tg://user?id={userid}'>{userid}</a>"
    else:
        await message.answer("This message neither forwarded from private chat nor includes a valid user id. Forward a message from the private chat to here (Make sure the message was sent by a user)\n\nOr send the user id")
        return
    exist = db.fetchone("SELECT idx, allowed FROM users WHERE userid=%s::text", (userid,))
    if exist:
        if exist[1] == 2:
            await message.answer(f"{mention} already has manual access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
        else:
            db.query("UPDATE users SET allowed = 2 WHERE idx = %s", (exist[0],))
            await message.answer(f"{mention} has been given manual access to the bot. User won't need to join required channels.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
    db.query("INSERT INTO users (userid, allowed) VALUES (%s, 2)", (userid,))
    await message.answer(f"{mention} has been given manual access to the bot. User won't need to join required channels.\n\nBack to the access menu.")
    await state.set_state(accstates.manl)
    await message.answer("You can give or remove access to users manually here", reply_markup=man_access)

@access.callback_query(F.data == "remove_access")
async def remove_access_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(accstates.rema)
    await callback.message.answer("Forward the message of the user you want to remove access to the bot, or give the id of the user.", reply_markup=back_key)
    await callback.message.delete()

@access.message(F.text == dict.back, accstates.rema)
async def back_to_r(message: types.Message, state: FSMContext) -> None:
    await message.answer("Back to the access menu.", reply_markup=main_key)
    await state.set_state(accstates.manl)
    await message.answer("You can give or remove access to users manually here", reply_markup=man_access)

@access.message(accstates.rema)
async def remove_access(message: types.Message, state: FSMContext) -> None:
    if message.forward_from:
        userid = message.forward_from.id
        username = message.forward_from.username
        mention = message.forward_from.mention_html()
    elif message.text.isnumeric():
        userid = int(message.text)
        mention = f"<a href='tg://user?id={userid}'>{userid}</a>"
    else:
        await message.answer("This message neither forwarded from private chat nor includes a valid user id. Forward a message from the private chat to here (Make sure the message was sent by a user)\n\nOr send the user id")
        return
    exist = db.fetchone("SELECT idx, allowed FROM users WHERE userid=%s::text", (userid,))
    if exist:
        if exist[1] == -1:
            await message.answer(f"{mention} already doesn't have access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
        else:
            db.query("UPDATE users SET allowed = -1 WHERE idx = %s", (exist[0],))
            await message.answer(f"{mention} has been removed access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
    db.query("INSERT INTO users (userid, allowed) VALUES (%s, -1)", (userid,))
    await message.answer(f"{mention} has been denied access to the bot.\n\nBack to the access menu.")
    await state.set_state(accstates.manl)
    await message.answer("You can give or remove access to users manually here", reply_markup=man_access)

@access.callback_query(F.data == "confirm", accstates.confirm)
async def confirm_add_chat(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    chid = data.get("chid")
    title = data.get("title")
    link = data.get("link")
    chck = db.fetchone("SELECT title FROM channel WHERE chid = %s", (str(chid),))
    if chck:
        await callback.message.answer(f"This channel already has been set as a permission giving chat with title <b>{chck[0]}</b>", reply_markup=main_key)
        await callback.answer("Already added")
        await state.set_state(accstates.post)
        response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
        channels = db.fetchall("SELECT title, link, idx FROM channel")
        if not channels:
            response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
        await callback.message.answer(response, reply_markup=post_chan(channels))
        return
    db.query("INSERT INTO channel (chid, title, link) VALUES (%s, %s, %s)", (str(chid), title, link))
    await callback.answer(f"Successfully added")
    await callback.message.answer("Chat successfully added!", reply_markup=main_key)
    await callback.message.delete()
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    await callback.message.answer(response, reply_markup=post_chan(channels))

@access.callback_query(F.data == "cancel", accstates.confirm)
async def cancel_add_chat(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Operation cancelled")
    await callback.message.answer("Operation cancelled", reply_markup=main_key)
    await callback.message.delete()
    await state.set_state(accstates.post)
    response = "Here you can manage the permission giving chats.\n\nThe bot will automatically give permissions to users who are members of any of the following chats."
    channels = db.fetchall("SELECT title, link, idx FROM channel")
    if not channels:
        response = "No chats have been set for automatic permissions. You can add chats that users will need to join to get permission to use the bot."
    await callback.message.answer(response, reply_markup=post_chan(channels))

# Helper function for auto-deleting messages after a delay
async def delete_after_delay(message, delay_seconds):
    """Delete a message after specified delay"""
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass  # Message might have been deleted already