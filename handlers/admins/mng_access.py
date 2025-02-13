from aiogram import types, Router, F, html
from data import config, dict
from keyboards.inline import access_menu, post_chan, mandconfirm, man_access
from keyboards.regular import main_key, back_key
from time import sleep
from states import accstates
from aiogram.fsm.context import FSMContext
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
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

@access.callback_query(CbData("post"), accstates.acmenu)
async def post_c(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.post)
    response = "Here you can change or reset the permission giving chat.\n\nThe bot will automatically give permissions to members of the following chat."
    channel = db.fetchone("SELECT title, link FROM channel")
    print(channel)
    if not channel:
        response = "The chat that users will be checked to give permission to the bot was not set, you can set a new one\n\nOnce you set a chat, the bot will automatically give permissions to members of that chat"
    await callback.message.edit_text(response, reply_markup=post_chan(channel))

@access.callback_query(CbData("back"), accstates.post)
async def back_to_s(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.acmenu)
    # await callback.message.answer(f"Menu: <b>{dict.settings}</b>", reply_markup=main_key)
    response = "Here you can manage the access of users to the bot"
    await callback.message.edit_text(response, reply_markup=access_menu)
    await callback.answer(f"Back to {dict.man_access} menu")

@access.callback_query(CbData("set_new"), accstates.post)
async def setnew(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(accstates.link)
    await callback.message.answer("Forward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id", reply_markup=back_key)
    await callback.message.delete()

@access.message(F.text == dict.back, accstates.link)
async def back_to_c(message: types.Message, state: FSMContext):
    await state.set_state(accstates.post)
    await message.answer("Back to posting channel menu", reply_markup=main_key)
    response = "Here you can change or reset the permission giving chat.\n\nThe bot will automatically give permissions to members of the following chat."
    channel = db.fetchone("SELECT title, link FROM channel")
    print(channel)
    if not channel:
        response = "The chat that users will be checked to give permission to the bot was not set, you can set a new one\n\nOnce you set a chat, the bot will automatically give permissions to members of that chat"
    await message.answer(response, reply_markup=post_chan(channel))

@access.message(accstates.link)
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
async def back_to_link(message: types.Message, state: FSMContext) -> None:
    await state.set_state(accstates.link)
    await message.answer("This time do it correctly.\n\nForward a message from the private chat to here (Make sure the message was sent by the group as anonymous)\n\nOr send the chat id", reply_markup=back_key)

@access.callback_query(CbData("reset"), accstates.post)
async def reset(callback: types.CallbackQuery, state: FSMContext) -> None:
    # old = db.fetchone("SELECT title, link, chid FROM channel")
    db.query("DELETE FROM channel")
    # db.query("INSERT INTO channel (chid, title, link) VALUES (%s, %s, %s)", (config.bot_info.id, config.bot_info.username, f"https://t.me/{config.bot_info.username}"))
    await callback.answer("Reset successfull")
    await post_c(callback, state)

@access.callback_query(accstates.confirm)
async def confirm(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data == "cancel":
        await callback.answer("Cancelled")
        await callback.message.answer("Back to auto-permit menu", reply_markup=main_key)
        await post_c(callback, state)
        # await callback.message.delete()
        return
    data = await state.get_data()
    chid = data.get("chid")
    title = data.get("title")
    link = data.get("link")
    chck = db.fetchone("SELECT title FROM channel WHERE chid = %s", (chid,))
    if chck:
        msg = await callback.message.answer(f"This channel already has been set as the permission giving chat")
        await callback.answer("Already this one")
        await callback.message.answer("Back to auto-permit menu", reply_markup=main_key)
        await post_c(callback, state)
        sleep(2)
        await msg.delete()
        # await callback.message.delete()
        return
    chck = db.fetchone("SELECT title FROM channel")
    if chck:
        db.query("DELETE FROM channel")
    # db.query("DELETE FROM channel")
    db.query("INSERT INTO channel (chid, title, link) VALUES (%s, %s, %s)", (chid, title, link))
    await callback.answer(f"Successfully set")
    await callback.message.answer("Back to posting channel menu", reply_markup=main_key)
    await post_c(callback, state)
    # await callback.message.delete()


@access.callback_query(CbData("manually"))
async def manually(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(accstates.manl)
    await callback.message.edit_text("You can give or remove access to users manually here", reply_markup=man_access)
    # await callback.message.delete()

@access.callback_query(CbData("back"), accstates.manl)
async def back_to_m(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(f"Back to {html.bold(f"{dict.man_access}")} menu", reply_markup=main_key)
    await state.set_state(accstates.acmenu)
    await callback.message.answer(f"Here you can manage the access of users to the bot", reply_markup=access_menu)
    # sleep(1)
    await callback.message.delete()
    # await callback.message.delete()

@access.callback_query(CbData("add_access"))
async def add_access(callback: types.CallbackQuery, state: FSMContext) -> None:
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
        if exist[1]:
            await message.answer(f"{mention} already has access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
        else:
            db.query("UPDATE users SET allowed = 1 WHERE idx = %s", (exist[0],))
            await message.answer(f"{mention} has been given access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
    db.query("INSERT INTO users (userid, allowed) VALUES (%s, 1)", (userid,))

    await message.answer(f"{mention} has been given access to the bot.\n\nBack to the access menu.")
    await state.set_state(accstates.manl)
    await message.answer("You can give or remove access to users manually here", reply_markup=man_access)

@access.callback_query(CbData("remove_access"))
async def remove_access(callback: types.CallbackQuery, state: FSMContext) -> None:
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
        if not exist[1]:
            await message.answer(f"{mention} already doesn't have access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
        else:
            db.query("UPDATE users SET allowed = 0 WHERE idx = %s", (exist[0],))
            await message.answer(f"{mention} has been removed access to the bot.\n\nBack to the access menu.")
            await state.set_state(accstates.manl)
            await message.answer("You can give or remove access to users manually here", reply_markup=man_access)
            return
    await message.answer(f"{mention} already doesn't have access to the bot.\n\nBack to the access menu.")