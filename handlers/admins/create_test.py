from aiogram import Router, types, F, html
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
from loader import db
from keyboards.inline import today, ans_enter_meth, obom, ans_set_fin
from keyboards.regular import main_key, back_key, skip_desc
from data import dict, config
from datetime import datetime, timedelta, timezone
from states import creates
from aiogram.fsm.context import FSMContext
from utils.yau import get_text
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
    numq = int(message.text)
    try: 
        await state.update_data(numquest=numq)
    except:
        await message.answer(f"{await get_text(state)}\nPlease, send the number of questions using digits.")
        return
    if numq < 1 or numq > 100:
        await message.answer(f"{await get_text(state)}\nPlease, send the number of questions from 1 to 100.")
        return
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
    await message.answer(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers:", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.callback_query(CbData("today"), creates.sdate)
async def set_date_today(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(sdate=datetime.now(timezone(timedelta(hours=5))).strftime("%d %m %Y"))
    await query.message.edit_text(f"{await get_text(state)}\nPlease, choose the way you want to enter the answers:", reply_markup=ans_enter_meth)
    await state.set_state(creates.way)

@test.message(creates.way, F.text == dict.back)
async def back_to_date(message: types.Message, state: FSMContext):
    await message.answer(f"{await get_text(state)}\nPlease, send the date in the following format or press the following to set it for today:\n{html.code(f'DD MM YYYY')}", reply_markup=today)
    await state.set_state(creates.sdate)

@test.callback_query(CbData("all"), creates.way)
async def set_way_all(query: types.CallbackQuery, state: FSMContext):
    # await state.update_data(duration=None)
    # await state.update_data(ans=None)
    await query.message.edit_text(f"{await get_text(state)}\nPlease, send the answers in the following format:\n{html.code('Answer1\nAnswer2\nAnswer3,AgainAnswer3')}")
    await state.set_state(creates.ans)

@test.callback_query(CbData("one"), creates.way)
async def set_way_one(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(page=1)
    await state.update_data(curq=1)
    await state.update_data(type=1)
    await state.update_data(mcqnum=4)
    typesl = await state.get_data()
    donel = typesl.get("donel")
    typesl = typesl.get("typesl")
    numq = await state.get_data()
    numq = int(numq.get("numquest"))
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f"#1/{numq}")}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(1, numq, donel, 1, types))
    await state.set_state(creates.ans)

@test.callback_query(CbDataStartsWith("mcq_"), creates.ans)
async def set_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    # await state.update_data(ans=query.data.split("_")[1])
    cur_ans = query.data.split("_")[1]
    donel[curq] = cur_ans
    await query.answer(f"🟢 #{curq} is {cur_ans}")
    curq += 1
    await state.update_data(curq=curq)
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f"#{curq}/{numq}")}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq+1, numq, donel, type, typesl, mcqnum, page))
    await state.set_state(creates.ans)

@test.callback_query(creates.ans, CbDataStartsWith("test_"))
async def test_plus(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    sign = query.data.split("_")[1]
    if sign == "plus":
        if mcqnum == 6:
            await query.answer("Can't have more than 6 choices.")
            return
        else:
            mcqnum += 1
    elif sign == "minus":
        if mcqnum == 2:
            await query.answer("Can't have less than 2 choices.")
            return
        else:
            mcqnum -= 1
    await state.update_data(mcqnum=mcqnum)
    typesl[curq] = mcqnum
    await state.update_data(typesl=typesl)
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, type, typesl, mcqnum, page))

@test.callback_query(creates.ans, CbDataStartsWith("page_"))
async def browse_page(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = int(data.get("page"))
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    sign = query.data.split("_")[1]
    if sign == "next":
        if page == (numq+config.MAX_QUESTION_IN_A_PAGE-1)/config.MAX_QUESTION_IN_A_PAGE:
            await query.answer("You are already on the last page.")
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
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, type, typesl, mcqnum, page))

@test.callback_query(creates.ans, CbData("switch_open"))
async def switch_to_open(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    # type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    await state.update_data(type=0)
    await query.message.edit_text(f"Please, {html.underline("send")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, 0, typesl, mcqnum, page))

@test.callback_query(creates.ans, CbData("switch_mcq"))
async def switch_to_mcq(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    # type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    await state.update_data(type=1)
    await query.message.edit_text(f"Please, {html.underline("choose")} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, 1, typesl, mcqnum, page))

@test.callback_query(creates.ans, CbDataStartsWith("jump_"))
async def jump_to(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    curq = int(query.data.split("_")[1])
    type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    await state.update_data(curq=curq)
    await query.message.edit_text(f"Please, {html.underline('choose')} the right answer for question {html.bold(f'#{curq}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}", reply_markup=obom(curq, numq, donel, type, typesl, mcqnum, page))

@test.message(creates.ans)
async def get_open_ans(message: types.Message, state: FSMContext): # get open ended question's answer if not open ended ignore
    data = await state.get_data()
    print(data)
    curq = data.get("curq")
    type = data.get("type")
    typesl = data.get("typesl")
    numq = data.get("numquest")
    page = data.get("page")
    donel = data.get("donel")
    mcqnum = data.get("mcqnum")
    if type == 0:
        donel[curq] = message.text
        typesl[curq] = 0
        curq += 1
        if curq == numq:
            await state.set_state(creates.setts)
            await message.answer(f"{await get_text(state)}\nPlease, choose the right settings.", reply_markup=ans_set_fin(1, 1))
            return
        await state.update_data(curq=curq)
        await state.update_data(donel=donel)
        await state.update_data(typesl=typesl)
        await state.update_data(type=1)
        await message.answer(f"Please, {html.underline('choose')} the right answer for question {html.bold(f'#{curq+1}/{numq}')}:\n\n{html.blockquote("ps. 🟢 - done, 🟡 - current, 🔴 - not done (yes, traffic lights, you dumb*ss)")}")
    else:
        msg = await message.answer("Not in open ended mode.")
        
        await message.delete()
        sleep(2)
        await msg.delete()