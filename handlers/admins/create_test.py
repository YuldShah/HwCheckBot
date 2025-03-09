from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import today, ans_enter_meth, obom, ans_set_fin, inl_folders, remove_att
from keyboards.regular import main_key, back_key, skip_desc, adm_default
from keyboards.regular import attach_done_for_create
from data import dict, config
from datetime import datetime, timedelta, timezone
from states import creates
from aiogram.fsm.context import FSMContext
from utils.yau import get_text, get_ans_text
from time import sleep
import json
import re

test = Router()

test.message.filter(IsAdmin())
test.callback_query.filter(IsAdminCallback())


@test.message(F.text == dict.cr_test)
async def create_test(message: types.Message, state: FSMContext):
    await message.answer(f"Please, send the title.", reply_markup=main_key)
    await state.set_state(creates.title)
    await state.update_data(title=None)
    await state.update_data(about=None)
    await state.update_data(instructions=None)
    await state.update_data(numquest=None)
    await state.update_data(sdate=None)
    # await state.update_data(duration=None)
    # title=data.get("title")
    # about=data.get("about")
    # instructions=data.get("instructions")
    # numquest=data.get("numquest")
    # sdate=data.get("sdate")
    # duration=data.get("duration")

@test.message(creates.title)
async def get_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.about, F.text == dict.skip)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=None)
    await message.answer(f"{await get_text(state)}\nPlease, send the instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.about, F.text==dict.back)
async def back_to_title(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the title.", reply_markup=main_key)
    await state.set_state(creates.title)

@test.message(creates.about)
async def get_about(message: types.Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.instructions, F.text == dict.skip)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=None, attaches=[])
    await state.set_state(creates.attachments)
    await message.answer(f"{await get_text(state)}\nPlease, send the attachments if any and press done if you're.", reply_markup=attach_done_for_create)

@test.message(creates.instructions, F.text == dict.back)
async def back_to_about(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.instructions)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=message.text, attaches=[])
    await state.set_state(creates.attachments)
    await message.answer(f"{await get_text(state)}\nPlease, send the attachments if any and press done if you're.", reply_markup=attach_done_for_create)

@test.message(creates.attachments, F.text == dict.done)
async def done_attachments(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.attachments, F.text == dict.back)
async def back_to_instructions(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

@test.message(creates.attachments)
async def get_attachments(message: types.Message, state: FSMContext):
    data = await state.get_data()
    attaches = data.get("attaches")
    num = 1
    if not attaches:
        attaches = []
    else:
        num = attaches[-1][0] + 1
    if message.photo:
        attaches.append((num, message.photo[-1].file_id, message.caption, "photo"))
    elif message.document:
        attaches.append((num, message.document.file_id, message.caption, "document"))
    else:
        await message.answer(f"{await get_text(state)}\n❗️ Please, send only photos or documents.")
        return
    await state.update_data(attaches=attaches)
    await message.reply(f"🗃 Attachment {html.bold(f"#{len(attaches)}")} added.\n\nSend more attachments if needed or press done.", reply_markup=attach_done_for_create)
    

@test.message(creates.number, F.text == dict.back)
async def back_to_instructions(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(creates.attachments)
    attaches = data.get("attaches")
    if attaches:
        for idx, fileid, caption, ty in attaches:
            # attach_from_db = db.fetchone("SELECT idx, tgfileid, caption FROM attachments WHERE id = %s", (i,))
            if ty == "document":
                await message.answer_document(document=fileid, caption=caption, reply_markup=remove_att(idx)) 
            elif ty == "photo":
                await message.answer_photo(photo=fileid, caption=caption, reply_markup=remove_att(idx))
            else:
                await message.answer(f"Attachment {html.bold(f"#{idx}")} type not recognized.")
    await message.answer(f"Delete the unwanted attachments by clicking on them.\n\nAnd send new attachments for the test with captions if needed.", reply_markup=attach_done_for_create)

@test.callback_query(CbDataStartsWith("rma_"), creates.attachments)
async def remove_attach(query: types.CallbackQuery, state: FSMContext):
    idx = int(query.data.split("_")[1])
    data = await state.get_data()
    attaches = data.get("attaches")
    for i in range(len(attaches)):
        if attaches[i][0] == idx:
            attaches.pop(i)
            break
    await state.update_data(attaches=attaches)
    await query.answer("Attachment removed.")
    await query.message.delete()

@test.message(creates.number)
async def get_number(message: types.Message, state: FSMContext):
    numq = None
    try: 
        numq = int(message.text)
    except:
        await message.answer(f"{await get_text(state)}\n❗️ Please, send the number of questions using digits.")
        return
    if numq < 1 or numq > 100:
        await message.answer(f"{await get_text(state)}\n❗️ Please, send the number of questions from 1 to 100.")
        return
    await state.update_data(numquest=numq, vis=1, resub=0, folder=None)
    await state.update_data(donel=[None for i in range(numq)])
    await state.update_data(typesl=[config.MULTIPLE_CHOICE_DEF for i in range(numq)])
    await message.answer(f"{await get_text(state)}\nPlease, send the deadline in one of the following formats:\n"
                         f"- Time only: \"HH\", \"HH MM\", \"HH:MM\" (sets for today)\n"
                         f"- Date only: \"DD MM YYYY\" (sets time to 23:59)\n"
                         f"- Full: \"HH:MM DD MM YYYY\"", reply_markup=today)
    await state.set_state(creates.sdate)

@test.message(creates.sdate, F.text == dict.back)
async def back_to_number(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

def parse_datetime(input_str: str) -> datetime:
    now = datetime.now(timezone(timedelta(hours=5)))
    parts = input_str.strip().split()
    if len(parts) == 1:
        # Only time provided
        if ':' in parts[0]:
            h_str, m_str = parts[0].split(':')
        else:
            h_str, m_str = parts[0], "00"
        dt = now.replace(hour=int(h_str), minute=int(m_str), second=0, microsecond=0)
    elif len(parts) == 2:
        # Time provided as HH MM
        h_str, m_str = parts[0], parts[1]
        dt = now.replace(hour=int(h_str), minute=int(m_str), second=0, microsecond=0)
    elif len(parts) == 3:
        # Only date provided: DD MM YYYY
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        dt = now.replace(year=year, month=month, day=day, hour=23, minute=59, second=0, microsecond=0)
    elif len(parts) >= 4:
        # Time and date provided: HH:MM DD MM YYYY
        if ':' in parts[0]:
            h_str, m_str = parts[0].split(':')
            day = int(parts[1])
            month = int(parts[2])
            year = int(parts[3]) if len(parts) >= 4 else now.year
            dt = now.replace(year=year, month=month, day=day, hour=int(h_str), minute=int(m_str), second=0, microsecond=0)
        else:
            raise ValueError("Invalid date/time format")
    else:
        raise ValueError("Invalid date/time format")
    return dt

@test.message(creates.sdate)
async def get_sdate(message: types.Message, state: FSMContext):
    try:
        dt = parse_datetime(message.text)
    except ValueError:
        await message.answer(f"{await get_text(state)}\n❗️ Please, send the deadline using one of the following formats:\n"
                             f"- Time only: \"HH\", \"HH MM\", \"HH:MM\" (sets for today)\n"
                             f"- Date only: \"DD MM YYYY\" (sets time to 23:59)\n"
                             f"- Full: \"HH:MM DD MM YYYY\"")
        return
    now = datetime.now(timezone(timedelta(hours=5)))
    if dt < now:
        await message.answer(f"{await get_text(state)}\n❗️ The deadline must be in the future.")
        return
    await state.update_data(sdate=dt)  # Store as datetime object
    await message.answer(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers (multiple answers only possible with all at once option):", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.callback_query(CbData("today"), creates.sdate)
async def set_date_today(query: types.CallbackQuery, state: FSMContext):
    now = datetime.now(timezone(timedelta(hours=5)))
    dt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    await state.update_data(sdate=dt)
    await query.message.edit_text(
        f"{await get_text(state)}\nDeadline set to: {dt.strftime('%H:%M %d %m %Y')}\nPlease, choose the way you want to enter the answers (multiple answers only possible with all at once option):",
        reply_markup=ans_enter_meth
    )
    await state.set_state(creates.way)

@test.message(creates.way, F.text == dict.back)
async def back_to_date(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the date in the following format or press the following to set it for today:\n{html.code(f'DD MM YYYY')}", reply_markup=today)
    await state.set_state(creates.sdate)

@test.callback_query(CbData("all"), creates.way)
async def set_way_all(query: types.CallbackQuery, state: FSMContext):
    # await state.update_data(duration=None)
    # await state.update_data(ans=None)
    await state.update_data(entering="all")
    await query.message.edit_text(f"{await get_text(state)}\nPlease, send the answers in the following format:\n{html.code('Answer1\nAnswer2\nAnswer3,AgainAnswer3')}")
    await state.set_state(creates.ans)

@test.callback_query(CbData("one"), creates.way)
async def set_way_one(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(page=1, curq=1)
    data = await state.get_data()
    donel = data.get("donel")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    ans_confirm = data.get("ans_confirm")
    await state.update_data(entering="one")
    await query.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#1/{numq}')}:",
        reply_markup=obom(1, numq, donel, typesl, page, ans_confirm)
    )
    await state.set_state(creates.ans)

@test.callback_query(F.data.startswith("mcq_"), creates.ans)
async def set_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    # Switch to MCQ by setting the current question's typesl to default (nonzero)
    from data import config
    # typesl[curq-1] = config.MULTIPLE_CHOICE_DEF
    # await state.update_data(typesl=typesl)
    donel = data.get("donel")
    numq = data.get("numquest")
    page = data.get("page")
    cur_ans = query.data.split("_")[1]
    donel[curq-1] = cur_ans
    ans_confirm = bool(data.get("ans_confirm"))
    await query.answer(f"🟢 #{curq} is {cur_ans}")
    new_cur = -1
    for i in range(len(donel)):
        if not donel[i]:
            new_cur = i+1
            break
    if new_cur == -1:
        # await state.set_state(creates.setts)
        vis = data.get("vis")
        resub = data.get("resub")
        folder = data.get("folder")
        # await state.update_data(vis=0, resub=0, folder=None)
        await query.message.edit_text(f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose' if typesl[curq-1] > 0 else 'send')} the right answer for question {html.bold(f'#{curq}/{numq}')}:"
            f"\n\n{html.bold('Note: you have entered all the answers. You can change the answers for each question by clicking on the question number, navigating through pages.')}",
            reply_markup=obom(curq, numq, donel, typesl, page, confirm=True)
        )
        await state.update_data(ans_confirm=True)
        # await state.set_state(creates.ans_confirm)
        # await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(1, 1))
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    page = new_page
    await state.update_data(curq=new_cur, donel=donel, page=page)
    await query.message.edit_text(f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
        reply_markup=obom(new_cur, numq, donel, typesl, page, ans_confirm)
    )
    # await state.set_state(creates.ans)

@test.callback_query(creates.ans, CbDataStartsWith("test_"))
async def test_plus(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    ans_confirm = bool(data.get("ans_confirm"))
    sign = query.data.split("_")[1]
    if sign == "plus":
        if typesl[curq-1] == 6:
            await query.answer("Can't have more than 6 choices.")
            return    
        typesl[curq-1] += 1
    elif sign == "minus":
        if typesl[curq-1] == 2:
            await query.answer("Can't have less than 2 choices.")
            return
        if donel[curq-1] is not None:
            diff = ord(donel[curq-1])-ord("A")
            if diff+1 == typesl[curq-1]:
                await query.answer("Can't have less choices than the answer.")
                return
        typesl[curq-1] -= 1
    await query.answer(f"Now {typesl[curq-1]} choices.")
    await state.update_data(typesl=typesl)
    await query.message.edit_text(f"{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}\n\n{get_ans_text(donel, typesl)}\n\nPlease, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:", reply_markup=obom(curq, numq, donel, typesl, page, ans_confirm))

@test.callback_query(creates.ans, CbDataStartsWith("page_"))
async def browse_page(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = int(data.get("page"))
    donel = data.get("donel")
    ans_confirm = bool(data.get("ans_confirm"))
    sign = query.data.split("_")[1]
    if sign == "next":
        if page == (numq+config.MAX_QUESTION_IN_A_PAGE-1)//config.MAX_QUESTION_IN_A_PAGE:
            await query.answer("You are already on the last page.")
            return
        page += 1
    elif sign == "prev":
        if page == 1:
            await query.answer("You are already on the first page.")
            return
        page -= 1
    else:
        await query.answer("There just for decoration ;)")
        return
    await state.update_data(page=page)
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{get_ans_text(donel, typesl)}\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, typesl, page, ans_confirm))

@test.callback_query(creates.ans, CbData("switch_open"))
async def switch_to_open(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    ans_confirm = bool(data.get("ans_confirm"))
    # Switch to open ended mode by setting current typesl to 0
    typesl[curq-1] = 0
    await state.update_data(typesl=typesl)
    donel = data.get("donel")
    numq = data.get("numquest")
    page = data.get("page")
    await state.update_data(msg=query.message.message_id)
    await query.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('send')} the right answer for question {html.bold(f'#{curq}/{numq}')}:",
        reply_markup=obom(curq, numq, donel, typesl, page, ans_confirm)
    )

@test.callback_query(creates.ans, CbData("switch_mcq"))
async def switch_to_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    from data import config
    # Switch to MCQ mode by setting current typesl to a default value
    typesl[curq-1] = config.MULTIPLE_CHOICE_DEF
    await state.update_data(typesl=typesl)
    donel = data.get("donel")
    numq = data.get("numquest")
    page = data.get("page")
    ans_confirm = bool(data.get("ans_confirm"))
    await query.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{curq}/{numq}')}:",
        reply_markup=obom(curq, numq, donel, typesl, page, ans_confirm)
    )

@test.callback_query(creates.ans, CbDataStartsWith("jump_"))
async def jump_to(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_cur = int(query.data.split("_")[1])
    curq = data.get("curq")
    if new_cur == curq:
        await query.answer(f"Already at #{new_cur}")
        return
    donel = data.get("donel")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    ans_confirm = bool(data.get("ans_confirm"))
    await state.update_data(curq=new_cur)
    if typesl[new_cur-1] == 0:
        await query.message.edit_text(
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('send')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            reply_markup=obom(new_cur, numq, donel, typesl, page, ans_confirm)
        )
    else:
        await query.message.edit_text(
            
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            reply_markup=obom(new_cur, numq, donel, typesl, page, ans_confirm)
        )

@test.message(creates.ans, F.text == dict.back)
async def back_to_way(message: types.Message, state: FSMContext):
    # data = await sta/te.get_data()
    # curq = data.get("curq")
    # typesl = data.get("typesl")
    # numq = data.get("numquest")
    # page = data.get("page")
    # donel = data.get("donel")
    # entering = data.get("entering")
    # if entering != "all":

    # await state.update_data(entering=None)
    await message.answer(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers (multiple answers only possible with all at once option):", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.message(creates.ans)
async def get_open_ans(message: types.Message, state: FSMContext):
    data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    if data.get("entering") == "all":
        ans = []
        lines = message.text.split("\n")
        cnt = 0
        for line in lines:
            if not line:
                continue
            if "," in line:
                line = [item.strip() for item in line.split(",")]
            ans.append(line)
            cnt += 1
        if cnt == numq:
            donel = ans
            # await state.update_data(donel=donel)
            for i in range(len(donel)):
                qtype = typesl[i]
                if type(donel[i]) == list:
                    for j in donel[i]:
                        if len(j) > 1 or j not in ["A", "B", "C", "D", "E", "F"]:
                            typesl[i] = 0
                        else:
                            typesl[i] = max(typesl[i], ord(j) - ord("A") + 1)
                else:
                    if len(donel[i]) > 1 or donel[i] not in ["A", "B", "C", "D", "E", "F"]:
                        typesl[i] = 0
                    else:
                        typesl[i] = max(typesl[i], ord(donel[i]) - ord("A") + 1)
            await state.update_data(typesl=typesl, donel=donel)
            await state.update_data(donel=donel)
            vis = data.get("vis")
            resub = data.get("resub")
            folder = data.get("folder")
            msg = await message.answer(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub, folder)
            )
            await state.update_data(msg=msg.message_id)
            await state.set_state(creates.setts)
            return
        else:
            await message.answer(f"Please, send all the answers.\nLooks like you have only {cnt}/{numq} answers.")
            return

    curq = data.get("curq")
    donel = data.get("donel")
    page = data.get("page")
    msg = data.get("msg")
    ans_confirm = bool(data.get("ans_confirm"))
    if typesl[curq-1] == 0:
        donel[curq-1] = message.text
        # bruh = await message.answer(f"🟢 #{curq} is {message.text}")
        new_cur = -1
        for i in range(len(donel)):
            if not donel[i]:
                new_cur = i+1
                break
        if new_cur == -1:
            await state.set_state(creates.setts)
            await state.update_data(curq=new_cur, donel=donel, page=page)
            vis = data.get("vis")
            resub = data.get("resub")
            folder = data.get("folder")
            await message.answer(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish.", reply_markup=ans_set_fin(vis, resub, folder))
            return
        new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
        page = new_page
        await state.update_data(curq=new_cur, donel=donel, page=page)
        # Optionally, if you want to switch back to MCQ after an open answer, uncomment below:
        # from data import config
        # if typesl[new_cur-1] == 0:
        #     typesl[new_cur-1] = config.MULTIPLE_CHOICE_DEF
        #     await state.update_data(typesl=typesl)
        print(msg)
        
        await message.bot.edit_message_text(f"Please, {html.underline('send')} the right answer for question {html.bold(f'#{curq}/{numq}')}:", chat_id=message.chat.id, message_id=msg)
        await message.answer(
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            # chat_id=message.chat.id,
            # message_id=msg.message_id,
            reply_markup=obom(new_cur, numq, donel, typesl, page, ans_confirm)
        )
        # await state.set_state(creates.setts)
        # await message.delete()
        # await msg.delete()
    else:
        msg = await message.answer("Not in open ended mode.")
        await message.delete()
        sleep(2)
        await msg.delete()

@test.message(creates.setts, F.text == dict.back)
async def back_to_ans(message: types.Message, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    entering = data.get("entering")
    await state.set_state(creates.ans)
    if entering == "all":
        await message.answer(f"{await get_text(state)}\nPlease, send the answers in the following format:\n{html.code('Answer1\nAnswer2\nAnswer3,AgainAnswer3')}")
        return
    else:
        await message.answer(
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose' if typesl[curq-1] > 0 else 'send')} the right answer for question {html.bold(f'#{curq}/{numq}')}:"
            f"\n\n{html.bold('Note: you have entered all the answers. You can change the answers for each question by clicking on the question number, navigating through pages.')}",
            
            reply_markup=obom(curq, numq, donel, typesl, page, confirm=True))
        await state.update_data(ans_confirm=True)

@test.callback_query(CbData("continue"), creates.ans)
async def confirm_ans(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    vis = data.get("vis")
    resub = data.get("resub")
    folder = data.get("folder")
    await state.set_state(creates.setts)
    # await state.update_data()
    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub, folder))

# @test.callback_query(creates.setts, CbData("folder"))
# async def set_folder(query: types.CallbackQuery, state: FSMContext):
#     folders = db.fetchall("SELECT * FROM folders")
#     if not folders:
#         await query.answer("No folders found, create one first")
#         return
#     await query.message.edit_text("Please, choose the folder:", reply_markup=inl_folders(folders))

@test.callback_query(creates.setts, CbData("back"))
async def back_to_ans(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    await state.set_state(creates.ans)
    await callback.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose' if typesl[curq-1] > 0 else 'send')} the right answer for question {html.bold(f'#{curq}/{numq}')}:"
        f"\n\n{html.bold('Note: you have entered all the answers. You can change the answers for each question by clicking on the question number, navigating through pages.')}",
        reply_markup=obom(curq, numq, donel, typesl, page, confirm=True)
    )
    await state.update_data(ans_confirm=True)
        # await state.set_state(creates.ans)


@test.callback_query(creates.setts, CbDataStartsWith("vis_"))
async def toggle_visibility(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    donel = data.get("donel")
    curq = data.get("curq")
    resub = data.get("resub")
    folder = data.get("folder")
    vis = query.data.split("_")[1]
    await query.answer(f"👁 Visibility now - {vis.capitalize()}.")
    # if vis == "on":
    #     await query.answer("Visibility now on.")
    # else:
    #     await query.answer("Visibility now off.")
        # vis = "off"
    await state.update_data(vis=vis=="on")

    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis=="on", resub, folder))

@test.callback_query(creates.setts, CbDataStartsWith("resub_"))
async def toggle_resubmission(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    donel = data.get("donel")
    curq = data.get("curq")
    resub = data.get("resub")
    folder = data.get("folder")
    vis = data.get("vis")
    resub = query.data.split("_")[1]
    await query.answer(f"Resubmission now - {resub.capitalize()}.")
    # if vis == "on":
    #     await query.answer("Visibility now on.")
    # else:
    #     await query.answer("Visibility now off.")
        # vis = "off"
    await state.update_data(resub=resub=="on")

    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub=="on", folder))

@test.callback_query(creates.setts, CbData("folder"))
async def set_folder(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    typesl = data.get("typesl")
    donel = data.get("donel")
    fd = data.get("folder")
    folders = db.fetchall("SELECT * FROM folders")
    if not folders:
        await query.answer("No folders found, create one first")
        return
    await state.set_state(creates.folder_change)
    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, choose the folder:", reply_markup=inl_folders(folders, fd))

@test.callback_query(F.data.startswith("folder_"), creates.folder_change)
async def change_folder_chosen(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fid = callback.data.split("_")[1]
    exid = data.get("exam_id")
    # folder_id = fid
    # db.query("UPDATE exams SET folder=%s WHERE idx=%s", (fid, exid,))
    folder = None
    if fid!="0":
        folder = db.fetchone("SELECT title FROM folders WHERE idx = %s", (fid,))[0]
    await state.update_data(folder_id=fid, folder=folder)
    await callback.answer("Folder changed successfully")
    # await callback.message.edit_text("🗂 Folder changed successfully")
    # data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    donel = data.get("donel")
    curq = data.get("curq")
    resub = data.get("resub")
    # folder = fid
    vis = data.get("vis")
    # await callback.answer(f"👁 Visibility now - {vis.capitalize()}.")
    # if vis == "on":
    #     await query.answer("Visibility now on.")
    # else:
    #     await query.answer("Visibility now off.")
        # vis = "off"
    # await state.update_data(vis=vis=="on")
    await state.set_state(creates.setts)
    await callback.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub, folder))

@test.callback_query(F.data == "back", creates.folder_change)
async def back_to_idk(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    donel = data.get("donel")
    curq = data.get("curq")
    resub = data.get("resub")
    folder = data.get("folder")
    vis = data.get("vis")
    # await state.update_data(vis=vis=="on")
    await state.set_state(creates.setts)
    await callback.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis, resub, folder))


@test.callback_query(creates.setts, CbData("continue"))
async def finalize_test(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text("Saving the test, please wait...")
    data = await state.get_data()
    title = data.get("title")
    about = data.get("about")
    instructions = data.get("instructions")
    numquest = data.get("numquest")
    sdate = data.get("sdate")  # Now a datetime object
    donel = data.get("donel")
    typesl = data.get("typesl")
    vis = not data.get("vis")
    resub = data.get("resub")
    folder_id = data.get("folder_id") or 0
    test_info = {"answers": donel, "types": typesl}
    query_str = """INSERT INTO exams (title, about, instructions, num_questions, correct, sdate, hide, resub, folder, random) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    random_text = datetime.now().strftime("%Y%m%d%H%M%S")
    db.query(query_str, (title, about, instructions, numquest, json.dumps(test_info), sdate, int(vis), int(resub), folder_id, random_text))
    attaches = data.get("attaches")
    exid = db.fetchone("SELECT idx FROM exams WHERE random = %s", (random_text,))[0]
    if attaches:
        for idx, fileid, caption, ty in attaches:
            db.query("INSERT INTO attachments (ty, tgfileid, caption, exid) VALUES (%s, %s, %s, %s)", (ty, fileid, caption, exid))
    await query.message.edit_text(f"📕 Test {html.bold(f"{title}")} created and stored successfully with its attachments.")
    await query.message.answer(f"Back to {html.bold(f"{dict.main_menu}")}", reply_markup=adm_default)
    await state.clear()