from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import today, ans_enter_meth, obom, ans_set_fin, inl_folders
from keyboards.regular import main_key, back_key, skip_desc
from data import dict, config
from datetime import datetime, timedelta, timezone
from states import creates
from aiogram.fsm.context import FSMContext
from utils.yau import get_text, get_ans_text
from time import sleep

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
    await state.update_data(instructions=None)
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.instructions, F.text == dict.back)
async def back_to_about(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new description.", reply_markup=skip_desc)
    await state.set_state(creates.about)

@test.message(creates.instructions)
async def get_instructions(message: types.Message, state: FSMContext):
    await state.update_data(instructions=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.number, F.text == dict.back)
async def back_to_instructions(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the new instructions.", reply_markup=skip_desc)
    await state.set_state(creates.instructions)

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
    await state.update_data(numquest=numq)
    await state.update_data(donel=[None for i in range(numq)])
    await state.update_data(typesl=[config.MULTIPLE_CHOICE_DEF for i in range(numq)])
    await message.answer(f"{await get_text(state)}\nPlease, send the date in the following format:\n{html.code(f"DD MM YYYY")}", reply_markup=today)
    await state.set_state(creates.sdate)

@test.message(creates.sdate, F.text == dict.back)
async def back_to_number(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the number of questions.", reply_markup=back_key)
    await state.set_state(creates.number)

@test.message(creates.sdate)
async def get_sdate(message: types.Message, state: FSMContext):

    await state.update_data(sdate=message.text)
    await message.answer(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers (multiple answers only possible with all at once option):", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.callback_query(CbData("today"), creates.sdate)
async def set_date_today(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(sdate=datetime.now(timezone(timedelta(hours=5))).strftime("%d %m %Y"))
    await query.message.edit_text(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers (multiple answers only possible with all at once option):", reply_markup=ans_enter_meth)
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
    # Remove any "type" updates
    data = await state.get_data()
    donel = data.get("donel")
    typesl = data.get("typesl")
    numq = int(data.get("numquest"))
    page = data.get("page")
    await query.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#1/{numq}')}:",
        reply_markup=obom(1, numq, donel, typesl, page)
    )
    await state.set_state(creates.ans)

@test.callback_query(CbDataStartsWith("mcq_"), creates.ans)
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
    await query.answer(f"🟢 #{curq} is {cur_ans}")
    new_cur = -1
    for i in range(len(donel)):
        if not donel[i]:
            new_cur = i+1
            break
    if new_cur == -1:
        await state.set_state(creates.setts)
        await state.update_data(vis=0, resub=0, folder=None)
        await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(1, 1))
        return
    new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
    page = new_page
    await state.update_data(curq=new_cur, donel=donel, page=page)
    await query.message.edit_text(f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
        reply_markup=obom(new_cur, numq, donel, typesl, page)
    )
    await state.set_state(creates.ans)

@test.callback_query(creates.ans, CbDataStartsWith("test_"))
async def test_plus(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
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
        typesl[curq-1] -= 1
    await query.answer(f"Now {typesl[curq-1]} choices.")
    await state.update_data(typesl=typesl)
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{get_ans_text(donel, typesl)}\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, typesl, page))

@test.callback_query(creates.ans, CbDataStartsWith("page_"))
async def browse_page(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = int(data.get("page"))
    donel = data.get("donel")
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
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{get_ans_text(donel, typesl)}\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, typesl, page))

@test.callback_query(creates.ans, CbData("switch_open"))
async def switch_to_open(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
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
        reply_markup=obom(curq, numq, donel, typesl, page)
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
    await query.message.edit_text(
        f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
        f"\n\n{get_ans_text(donel, typesl)}"
        f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{curq}/{numq}')}:",
        reply_markup=obom(curq, numq, donel, typesl, page)
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
    await state.update_data(curq=new_cur)
    if typesl[new_cur-1] == 0:
        await query.message.edit_text(
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('send')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            reply_markup=obom(new_cur, numq, donel, typesl, page)
        )
    else:
        await query.message.edit_text(
            
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            reply_markup=obom(new_cur, numq, donel, typesl, page)
        )

@test.message(creates.ans, F.text == dict.back)
async def back_to_way(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # curq = data.get("curq")
    # typesl = data.get("typesl")
    # numq = data.get("numquest")
    # page = data.get("page")
    # donel = data.get("donel")
    await state.update_data(entering=None)
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
                line = list(line.split(","))
            ans.append(line)
            cnt += 1
        if cnt == numq:
            donel = ans
            # await state.update_data(donel=donel)
            for i in range(len(donel)):
                type = typesl[i]
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
            await state.update_data(curq=new_cur, donel=donel, page=page)
            await message.answer(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(1, 1)
            )
            await state.set_state(creates.setts)

        else:
            await message.answer(f"Please, send all the answers.\nLooks like you have only {cnt}/{numq} answers.")
            return

    curq = data.get("curq")
    donel = data.get("donel")
    page = data.get("page")
    msg = data.get("msg")
    if typesl[curq-1] == 0:
        donel[curq-1] = message.text
        msg = await message.answer(f"🟢 #{curq} is {message.text}")
        new_cur = -1
        for i in range(len(donel)):
            if not donel[i]:
                new_cur = i+1
                break
        if new_cur == -1:
            await state.set_state(creates.setts)
            await state.update_data(curq=new_cur, donel=donel, page=page)
            await message.answer(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish.", reply_markup=ans_set_fin(1, 1))
            return
        new_page = (new_cur-1)//config.MAX_QUESTION_IN_A_PAGE + 1
        page = new_page
        await state.update_data(curq=new_cur, donel=donel, page=page)
        # Optionally, if you want to switch back to MCQ after an open answer, uncomment below:
        # from data import config
        # if typesl[new_cur-1] == 0:
        #     typesl[new_cur-1] = config.MULTIPLE_CHOICE_DEF
        #     await state.update_data(typesl=typesl)
        await message.bot.edit_message_text(
            f"{html.blockquote('ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)')}"
            f"\n\n{get_ans_text(donel, typesl)}"
            f"\n\nPlease, {html.underline('choose')} the right answer for question {html.bold(f'#{new_cur}/{numq}')}:",
            chat_id=message.chat.id,
            message_id=msg,
            reply_markup=obom(new_cur, numq, donel, typesl, page)
        )
        await state.set_state(creates.setts)
        await message.delete()
        await msg.delete()
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
    await message.answer(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(curq, numq))
    await state.set_state(creates.setts)


@test.callback_query(creates.setts, CbData("folder"))
async def set_folder(query: types.CallbackQuery, state: FSMContext):
    folders = db.fetchall("SELECT * FROM folders")
    if not folders:
        await query.answer("No folders found, create one first")
        return
    await query.message.edit_text("Please, choose the folder:", reply_markup=inl_folders(folders))

@test.callback_query(creates.setts, CbData("back"))
async def back_to_ans(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curq = data.get("curq")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(curq, numq))



@test.callback_query(creates.setts, CbDataStartsWith("vis_"))
async def toggle_visibility(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    numq = data.get("numquest")
    typesl = data.get("typesl")
    donel = data.get("donel")
    curq = data.get("curq")
    resub = data.get("resub")
    vis = query.data.split("_")[1]
    if vis == "on":
        await query.answer("Visibility now on.")
    else:
        await query.answer("Visibility now off.")
    await state.update_data(vis=vis=="on")

    await query.message.edit_text(f"{await get_text(state)}\n{get_ans_text(donel, typesl)}\nPlease, change the settings as you wish. (Pressing toggles on/off)", reply_markup=ans_set_fin(vis=="on", ))