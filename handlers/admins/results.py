from aiogram import types, Router, F, html
from data import dict as dict_labels, config
from keyboards.regular import main_key
from keyboards.inline.adm_inline import stats_menu, user_selection_kb, exam_selection_kb, submission_details_kb, submission_detail_back_kb, export_select_menu
from states import statsstates
from aiogram.fsm.context import FSMContext
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone, timedelta
import json
import logging
import traceback
from utils.db.storage import DatabaseManager
from utils.yau import get_correct_text

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define UTC+5 timezone constant
UTC_PLUS_5 = timezone(timedelta(hours=5))

reser = Router()
reser.message.filter(IsAdmin())
reser.callback_query.filter(IsAdminCallback())

# Initialize database connection
db = DatabaseManager(config.DB_URL)

# Helper function to convert UTC datetime to UTC+5
def to_local_time(utc_dt):
    if utc_dt is None:
        return None
    
    # Ensure datetime has timezone info
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    # Convert to UTC+5
    return utc_dt.astimezone(UTC_PLUS_5)

# Helper function to format datetime for display
def format_datetime(dt):
    if dt is None:
        return "Not set"
    
    local_dt = to_local_time(dt)
    return local_dt.strftime('%Y-%m-%d %H:%M')

@reser.message(F.text == dict_labels.stats)
async def show_stats(message: types.Message, state: FSMContext):
    await message.answer(f"Menu {html.bold(f"{dict_labels.stats}")}", reply_markup=main_key)
    msg = await message.answer("📊 <b>Bot Statistics</b>\n\nLoading...")
    # Get basic statistics
    total_users = db.fetchone("SELECT COUNT(*) FROM users")[0]
    total_submissions = db.fetchone("SELECT COUNT(*) FROM submissions")[0]
    active_exams = db.fetchone("SELECT COUNT(*) FROM exams WHERE sdate > NOW()")[0]
    
    # Get recent submissions (last 5)
    recent_subs = db.fetchall("""
        SELECT s.idx, u.fullname, e.title, s.date 
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        ORDER BY s.date DESC LIMIT 5
    """)
    
    # Format the statistics message
    stats_message = f"📊 <b>Bot Statistics</b>\n\n"
    stats_message += f"👥 <b>Total Users:</b> {total_users}\n"
    stats_message += f"📝 <b>Total Submissions:</b> {total_submissions}\n"
    stats_message += f"⚡️ <b>Active Exams:</b> {active_exams}\n\n"
    
    stats_message += f"🕒 <b>Recent Submissions:</b>\n"
    subs = ""
    if recent_subs:
        for idx, sub in enumerate(recent_subs, 1):
            # Convert date to UTC+5
            local_date = format_datetime(sub[3])
            subs += f"{idx}. {html.bold(sub[1])} - {html.italic(sub[2])}: {local_date}\n"
    else:
        subs = "No recent submissions.\n"
    stats_message += html.blockquote(subs)
    
    await msg.edit_text(stats_message, reply_markup=stats_menu)
    await state.set_state(statsstates.stmenu)

@reser.callback_query(CbData("stats_all"), statsstates.stmenu)
async def show_all_submissions(callback: types.CallbackQuery, state: FSMContext):
    # Get total count for pagination
    total_submissions = db.fetchone("SELECT COUNT(*) FROM submissions")[0]
    submissions_per_page = config.SUBMISSIONS_PER_PAGE
    total_pages = (total_submissions + submissions_per_page - 1) // submissions_per_page
    
    # Store pagination info in state
    await state.update_data(
        page=1, 
        total_pages=total_pages,
        submissions_per_page=submissions_per_page,
        view_type="all"
    )
    
    await show_submissions_page(callback, state)
    await state.set_state(statsstates.viewing_all)

async def show_submissions_page(callback, state):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    submissions_per_page = data.get('submissions_per_page', 10)
    view_type = data.get('view_type', 'all')
    
    offset = (page - 1) * submissions_per_page
    
    query = """
        SELECT s.idx, u.fullname, e.title, s.date, s.answers, e.correct, e.sdate
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
    """
    
    if view_type == "by_user":
        user_id = data.get('selected_user')
        query += f" WHERE s.userid = '{user_id}'"
    elif view_type == "by_exam":
        exam_id = data.get('selected_exam')
        query += f" WHERE s.exid = {exam_id}"
    
    query += f" ORDER BY s.date DESC LIMIT {submissions_per_page} OFFSET {offset}"
    
    submissions = db.fetchall(query)
    
    if not submissions:
        await callback.answer("No submissions found.")
        return
    
    # Format submissions message
    message_text = f"📝 <b>Submissions</b>\n\n"
    
    for sub in submissions:
        sub_id, fullname, title, date, answers, correct, deadline = sub
        
        # Convert dates to UTC+5
        local_date = format_datetime(date)
        
        # Check if submission was late
        is_late = False
        if deadline and date > deadline:
            is_late = True
        
        try:
            # Log raw data for debugging
            logger.info(f"Processing submission {sub_id}")
            logger.info(f"Answers raw data: {answers}")
            logger.info(f"Correct raw data: {correct}")
            
            # Handle possible empty or invalid data
            if not answers or not correct:
                raise ValueError("Empty answer or correct data")
                
            answers_data = json.loads(answers if answers else "{}")
            correct_json = json.loads(correct if correct else "{}")
            
            # Check if answers are nested in a dict with 'answers' key (format used in some submissions)
            # Use built-in dict type instead of the imported dict module
            if isinstance(correct_json, dict) and 'answers' in correct_json:
                correct_data = correct_json['answers']
            else:
                correct_data = correct_json
                
            logger.info(f"Answers parsed: {type(answers_data)} {answers_data}")
            logger.info(f"Correct parsed: {type(correct_data)} {correct_data}")
            
            # Calculate score based on data type
            correct_count = 0
            total_questions = len(correct_data) if correct_data else 0
            
            if total_questions == 0:
                raise ValueError("No questions in correct data")
            
            # Handle different data structures using same approach as in users/results.py
            if isinstance(answers_data, dict) and isinstance(correct_data, list):
                # Convert dict to list if correct_data is list
                answers_list = []
                for i in range(1, len(correct_data) + 1):
                    q_num = str(i)
                    answers_list.append(answers_data.get(q_num, ""))
                
                for i, (answer, correct_answer) in enumerate(zip(answers_list, correct_data)):
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, list) and isinstance(correct_data, list):
                # Both are lists, use direct comparison
                for i, answer in enumerate(answers_data):
                    if i >= len(correct_data):
                        continue
                    correct_answer = correct_data[i]
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, dict) and isinstance(correct_data, dict):
                # Both are dicts, use key lookup
                for q_num, answer in answers_data.items():
                    if q_num in correct_data:
                        correct_answer = correct_data[q_num]
                        if isinstance(correct_answer, list):
                            if answer in correct_answer:
                                correct_count += 1
                        else:
                            if answer == correct_answer:
                                correct_count += 1
            else:
                # Fallback for other formats
                raise ValueError(f"Incompatible data types: answers={type(answers_data)}, correct={type(correct_data)}")
            
            score = f"{correct_count}/{total_questions}"
            percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            ab = ""
            message_text += html.bold(f"#{sub_id}")
            ab += f"👤 {html.bold(fullname)}\n"
            ab += f"📚 {html.bold(title or 'Unknown Test')}\n"
            ab += f"🕒 {local_date}"
            if is_late:
                ab += f"\n⚠️ <i>Late submission</i>"
            ab += f"\n✅ Score: {score} ({percentage:.1f}%)\n"

            message_text += html.blockquote(ab) + "\n"
        
        except Exception as e:
            # Log the error with traceback for debugging
            logger.error(f"Error calculating score for submission {sub_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add a more descriptive error message in the UI
            ab = ""
            message_text += html.bold(f"#{sub_id}")
            ab += f"👤 {html.bold(fullname or 'Unknown User')}\n"
            ab += f"📚 {html.bold(title or 'Unknown Test')}\n"
            ab += f"🕒 {local_date}"
            if is_late:
                ab += f"\n⚠️ <i>Late submission</i>"
            ab += f"\n❌ Error: Could not calculate score\n"

            message_text += html.blockquote(ab) + "\n"
    message_text += f"Showing {html.italic(len(submissions))}: {html.bold(str(submissions[-1][0]))} to {html.bold(str(submissions[0][0]))}\n"
    message_text += f"Page: {html.bold(page)} of {html.bold(total_pages)}"
    # Use the keyboard from adm_inline.py
    markup = submission_details_kb(submissions, page, total_pages)
    
    # Check if we need to edit or send a new message
    if callback.message and callback.message.text:
        await callback.message.edit_text(message_text, reply_markup=markup)
    else:
        await callback.message.answer(message_text, reply_markup=markup)
    
    await callback.answer()

@reser.callback_query(CbDataStartsWith("view_details_"))
async def view_submission_details(callback: types.CallbackQuery, state: FSMContext):
    sub_id = callback.data.split("_")[2]
    
    # Get submission details with deadline
    submission = db.fetchone("""
        SELECT s.idx, u.fullname, u.username, e.title, s.date, s.answers, e.correct, e.sdate
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        WHERE s.idx = %s
    """, (sub_id,))
    
    if not submission:
        await callback.answer("Submission not found.")
        return
    
    sub_id, fullname, username, title, date, answers_json, correct_json, deadline = submission
    
    # Convert dates to UTC+5
    local_date = format_datetime(date)
    local_deadline = format_datetime(deadline) if deadline else None
    
    # Check if submission was late
    is_late = False
    if deadline and date > deadline:
        is_late = True
    
    # Parse JSON data
    try:
        # Log raw data for debugging
        logger.info(f"Viewing submission {sub_id} details")
        logger.info(f"Answers raw: {answers_json}")
        logger.info(f"Correct raw: {correct_json}")
        
        if not answers_json or not correct_json:
            await callback.message.edit_text(
                f"📝 <b>Submission Details</b>\n\n"
                f"👤 <b>User:</b> {html.bold(fullname or 'Unknown')}\n"
                f"📚 <b>Test:</b> {html.bold(title or 'Unknown')}\n"
                f"🕒 <b>Date:</b> {local_date}\n\n"
                f"⚠️ This submission has no answer data or correct answer data.",
                reply_markup=submission_detail_back_kb()
            )
            return
            
        answers_dict = json.loads(answers_json)
        correct_json = json.loads(correct_json)
        
        # Check if answers are nested in a dict with 'answers' key
        # Use built-in dict type instead of the imported dict module
        if isinstance(correct_json, dict) and 'answers' in correct_json:
            correct_dict = correct_json['answers']
        else:
            correct_dict = correct_json
        
        logger.info(f"Answers parsed: {type(answers_dict)} {answers_dict}")
        logger.info(f"Correct parsed: {type(correct_dict)} {correct_dict}")
        
        # Special handling for empty data
        if not answers_dict or not correct_dict:
            await callback.message.edit_text(
                f"📝 <b>Submission Details</b>\n\n"
                f"👤 <b>User:</b> {html.bold(fullname or 'Unknown')}\n"
                f"📚 <b>Test:</b> {html.bold(title or 'Unknown')}\n"
                f"🕒 <b>Date:</b> {local_date}\n\n"
                f"⚠️ This submission has empty answer data or correct answer data.",
                reply_markup=submission_detail_back_kb()
            )
            return
        
        # Convert to list format for get_correct_text
        answers_list = []
        correct_list = []
        
        if isinstance(answers_dict, dict) and isinstance(correct_dict, list):
            # Convert dict to list format (used in results.py)
            for i in range(len(correct_dict)):
                q_num = str(i+1)
                answers_list.append(answers_dict.get(q_num, ""))
            correct_list = correct_dict
        elif isinstance(answers_dict, list) and isinstance(correct_dict, list):
            # Already in list format
            answers_list = answers_dict
            correct_list = correct_dict
        elif isinstance(answers_dict, dict) and isinstance(correct_dict, dict):
            # For dictionary format, convert to lists in order
            max_questions = max(len(answers_dict), len(correct_dict))
            for i in range(1, max_questions + 1):
                q_num = str(i)
                answers_list.append(answers_dict.get(q_num, ""))
                correct_list.append(correct_dict.get(q_num, ""))
        else:
            await callback.message.edit_text(
                f"📝 <b>Submission Details</b>\n\n"
                f"👤 <b>User:</b> {html.bold(fullname or 'Unknown')}\n"
                f"📚 <b>Test:</b> {html.bold(title or 'Unknown')}\n"
                f"🕒 <b>Date:</b> {local_date}\n\n"
                f"⚠️ Cannot display details: incompatible data formats.",
                reply_markup=submission_detail_back_kb()
            )
            return
        
        # Format detailed view using yau.py's get_correct_text
        details_text = f"📝 <b>Submission Details</b>\n\n"
        details_text += f"👤 <b>User:</b> {html.bold(fullname or 'Unknown')}"
        if username:
            details_text += f" (@{html.bold(username)})\n"
        else:
            details_text += "\n"
        details_text += f"📚 <b>Test:</b> {html.bold(title or 'Unknown')}\n"
        details_text += f"🕒 <b>Date:</b> {local_date}"
        if is_late:
            details_text += f"\n⚠️ <i>Late submission</i>"
        if local_deadline:
            details_text += f"\n⏰ <b>Deadline:</b> {local_deadline}"
        details_text += "\n\n"
        
        try:
            # Add score comparison using get_correct_text
            logger.info(f"Sending to get_correct_text: correct={correct_list}, answers={answers_list}")
            details_text += get_correct_text(correct_list, answers_list)
        except Exception as e:
            logger.error(f"Error in get_correct_text: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Fall back to manual scoring calculation
            correct_count = 0
            for i, (correct, answer) in enumerate(zip(correct_list, answers_list)):
                if correct == answer and correct and answer:
                    correct_count += 1
            
            total = len(correct_list)
            percentage = (correct_count / total) * 100 if total > 0 else 0
            
            details_text += f"<b>Manual score calculation:</b>\n"
            details_text += f"✅ Correct answers: {correct_count}/{total} ({percentage:.1f}%)\n\n"
            details_text += "<b>Answers vs Correct:</b>\n"
            
            for i, (correct, answer) in enumerate(zip(correct_list, answers_list)):
                match = "✅" if correct == answer and correct and answer else "❌"
                details_text += f"{i+1}. {html.code(str(answer))} {match}\n"
        
        # Create back button
        markup = submission_detail_back_kb()
        
        # Save current state data to restore it when going back
        await state.update_data(viewing_details=True)
        
        await callback.message.edit_text(details_text, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error processing submission details for {sub_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        await callback.message.edit_text(
            f"📝 <b>Submission Details</b>\n\n"
            f"❌ Error processing submission details: {str(e)}\n\n"
            f"This may be due to invalid data format in the database.",
            reply_markup=submission_detail_back_kb()
        )
    
    await callback.answer()

@reser.callback_query(CbData("back_to_submissions"), statsstates.viewing_all)
async def back_to_submissions_list_all(callback: types.CallbackQuery, state: FSMContext):
    await show_submissions_page(callback, state)
    await callback.answer()

@reser.callback_query(CbData("back_to_submissions"), statsstates.viewing_by_user)
async def back_to_submissions_list_user(callback: types.CallbackQuery, state: FSMContext):
    await show_submissions_page(callback, state)
    await callback.answer()

@reser.callback_query(CbData("back_to_submissions"), statsstates.viewing_by_exam)
async def back_to_submissions_list_exam(callback: types.CallbackQuery, state: FSMContext):
    await show_submissions_page(callback, state)
    await callback.answer()

@reser.callback_query(CbData("stats_prev_page"), statsstates.viewing_all)
async def prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    
    if page > 1:
        await state.update_data(page=page-1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("stats_next_page"), statsstates.viewing_all)
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    if page < total_pages:
        await state.update_data(page=page+1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("stats_jump_page_"), statsstates.viewing_all)
async def jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(page=target_page)
    await show_submissions_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(F.data == "stats_page_info", statsstates.viewing_all)
async def show_page_info(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Just to show the page info")

@reser.callback_query(CbData("stats_prev_page"), statsstates.viewing_by_user)
async def prev_page_user(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    
    if page > 1:
        await state.update_data(page=page-1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("stats_next_page"), statsstates.viewing_by_user)
async def next_page_user(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    if page < total_pages:
        await state.update_data(page=page+1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("stats_jump_page_"), statsstates.viewing_by_user)
async def jump_to_page_user(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(page=target_page)
    await show_submissions_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbData("stats_prev_page"), statsstates.viewing_by_exam)
async def prev_page_exam(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    
    if page > 1:
        await state.update_data(page=page-1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("stats_next_page"), statsstates.viewing_by_exam)
async def next_page_exam(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    if page < total_pages:
        await state.update_data(page=page+1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("stats_jump_page_"), statsstates.viewing_by_exam)
async def jump_to_page_exam(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(page=target_page)
    await show_submissions_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbData("stats_by_user"), statsstates.stmenu)
async def select_user(callback: types.CallbackQuery, state: FSMContext):
    # Get users who have submissions
    all_users = db.fetchall("""
        SELECT DISTINCT u.idx, u.userid, u.fullname, u.username FROM users u
        JOIN submissions s ON u.userid = s.userid
        ORDER BY u.fullname
    """)
    
    if not all_users:
        await callback.answer("No users with submissions found.")
        return
    
    # Setup pagination for users
    users_per_page = config.USERS_PER_PAGE
    total_pages = (len(all_users) + users_per_page - 1) // users_per_page
    page = 1
    
    # Store pagination info in state
    await state.update_data(
        all_users=all_users,
        users_page=page,
        users_total_pages=total_pages,
        users_per_page=users_per_page
    )
    
    await show_users_page(callback, state)
    await state.set_state(statsstates.select_user)

async def show_users_page(callback, state):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    users_per_page = data.get('users_per_page', config.USERS_PER_PAGE)
    all_users = data.get('all_users', [])
    
    # Calculate start and end indices for slicing
    start_idx = (page - 1) * users_per_page
    end_idx = min(start_idx + users_per_page, len(all_users))
    
    # Get users for current page
    current_page_users = all_users[start_idx:end_idx]
    
    if not current_page_users:
        await callback.answer("No users found for this page.")
        return
    
    await callback.message.edit_text(
        f"👤 <b>Select a user to view their submissions:</b> (Page: {page} of {total_pages})",
        reply_markup=user_selection_kb(current_page_users, page, total_pages)
    )

@reser.callback_query(CbData("users_prev_page"))
async def users_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    
    if page > 1:
        await state.update_data(users_page=page-1)
        await show_users_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("users_next_page"))
async def users_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    
    if page < total_pages:
        await state.update_data(users_page=page+1)
        await show_users_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("users_jump_page_"))
async def users_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(users_page=target_page)
    await show_users_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbDataStartsWith("stats_user_"), statsstates.select_user)
async def show_user_submissions(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_")[2]
    
    # Get user details
    user = db.fetchone("SELECT fullname FROM users WHERE userid = %s", (user_id,))
    
    if not user:
        await callback.answer("User not found.")
        return
    
    # Get submission count for pagination
    total_submissions = db.fetchone(
        "SELECT COUNT(*) FROM submissions WHERE userid = %s", 
        (user_id,)
    )[0]
    
    submissions_per_page = 10
    total_pages = (total_submissions + submissions_per_page - 1) // submissions_per_page
    
    # Store pagination info in state
    await state.update_data(
        page=1, 
        total_pages=total_pages,
        submissions_per_page=submissions_per_page,
        view_type="by_user",
        selected_user=user_id
    )
    
    await callback.answer(f"Showing submissions for {user[0]}")
    await show_submissions_page(callback, state)
    await state.set_state(statsstates.viewing_by_user)

@reser.callback_query(CbData("stats_by_exam"), statsstates.stmenu)
async def select_exam(callback: types.CallbackQuery, state: FSMContext):
    # Get exams with submissions
    all_exams = db.fetchall("""
        SELECT DISTINCT e.idx, e.title FROM exams e
        JOIN submissions s ON e.idx = s.exid
        ORDER BY e.title
    """)
    
    if not all_exams:
        await callback.answer("No exams with submissions found.")
        return
    
    # Setup pagination for exams
    exams_per_page = config.EXAMS_PER_PAGE
    total_pages = (len(all_exams) + exams_per_page - 1) // exams_per_page
    page = 1
    
    # Store pagination info in state
    await state.update_data(
        all_exams=all_exams,
        exams_page=page,
        exams_total_pages=total_pages,
        exams_per_page=exams_per_page
    )
    
    await show_exams_page(callback, state)
    await state.set_state(statsstates.select_exam)

async def show_exams_page(callback, state):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    exams_per_page = data.get('exams_per_page', config.EXAMS_PER_PAGE)
    all_exams = data.get('all_exams', [])
    
    # Calculate start and end indices for slicing
    start_idx = (page - 1) * exams_per_page
    end_idx = min(start_idx + exams_per_page, len(all_exams))
    
    # Get exams for current page
    current_page_exams = all_exams[start_idx:end_idx]
    
    if not current_page_exams:
        await callback.answer("No exams found for this page.")
        return
    
    await callback.message.edit_text(
        f"📚 <b>Select an exam to view submissions:</b> (Page: {page} of {total_pages})",
        reply_markup=exam_selection_kb(current_page_exams, page, total_pages)
    )

@reser.callback_query(CbData("exams_prev_page"))
async def exams_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    
    if page > 1:
        await state.update_data(exams_page=page-1)
        await show_exams_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("exams_next_page"))
async def exams_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    
    if page < total_pages:
        await state.update_data(exams_page=page+1)
        await show_exams_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("exams_jump_page_"))
async def exams_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(exams_page=target_page)
    await show_exams_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbDataStartsWith("stats_exam_"), statsstates.select_exam)
async def show_exam_submissions(callback: types.CallbackQuery, state: FSMContext):
    exam_id = callback.data.split("_")[2]
    
    # Get exam details
    exam = db.fetchone("SELECT title FROM exams WHERE idx = %s", (exam_id,))
    
    if not exam:
        await callback.answer("Exam not found.")
        return
    
    # Get submission count for pagination
    total_submissions = db.fetchone(
        "SELECT COUNT(*) FROM submissions WHERE exid = %s", 
        (exam_id,)
    )[0]
    
    submissions_per_page = 10
    total_pages = (total_submissions + submissions_per_page - 1) // submissions_per_page
    
    # Store pagination info in state
    await state.update_data(
        page=1, 
        total_pages=total_pages,
        submissions_per_page=submissions_per_page,
        view_type="by_exam",
        selected_exam=exam_id
    )
    
    await callback.answer(f"Showing submissions for {exam[0]}")
    await show_submissions_page(callback, state)
    await state.set_state(statsstates.viewing_by_exam)

@reser.callback_query(CbData("stats_export"))
async def export_excel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Preparing Excel file...")
    msg = await callback.message.edit_text("Preparing Excel file...\nThis may take a while.")
    # Get all submissions with details
    submissions = db.fetchall("""
        SELECT s.idx, u.fullname, u.username, e.title, s.date, s.answers, e.correct, u.userid, e.idx, e.sdate
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        ORDER BY s.date DESC
    """)
    
    if not submissions:
        await msg.edit_text("Couldn't found any submissions to export.")
        return
    
    # Prepare data for Excel
    data = []
    for sub in submissions:
        sub_id, fullname, username, title, date, answers, correct, user_id, exam_id, deadline = sub
        
        # Convert dates to UTC+5 for display in Excel
        local_date = format_datetime(date)
        local_deadline = format_datetime(deadline) if deadline else 'None'
        
        # Check if submission was late
        is_late = "No"
        if deadline and date > deadline:
            is_late = "Yes"
        
        # Handle different data formats for answers and correct answers
        try:
            # Log data for debugging
            logger.info(f"Processing export for submission {sub_id}")
            
            if not answers or not correct:
                raise ValueError("Empty answer or correct data")
                
            answers_data = json.loads(answers if answers else "{}")
            correct_json = json.loads(correct if correct else "{}")
            
            # Check if answers are nested in a dict with 'answers' key
            # Use built-in dict type instead of the imported dict module
            if isinstance(correct_json, dict) and 'answers' in correct_json:
                correct_data = correct_json['answers']
            else:
                correct_data = correct_json
            
            # Calculate score based on data type
            correct_count = 0
            total_questions = len(correct_data) if correct_data else 0
            
            if total_questions == 0:
                raise ValueError("No questions in correct data")
            
            # Handle different data structures using same approach as in users/results.py
            if isinstance(answers_data, dict) and isinstance(correct_data, list):
                # Convert dict to list if correct_data is list
                answers_list = []
                for i in range(1, len(correct_data) + 1):
                    q_num = str(i)
                    answers_list.append(answers_data.get(q_num, ""))
                
                for i, (answer, correct_answer) in enumerate(zip(answers_list, correct_data)):
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, list) and isinstance(correct_data, list):
                # Both are lists, use direct comparison
                for i, answer in enumerate(answers_data):
                    if i >= len(correct_data):
                        continue
                    correct_answer = correct_data[i]
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, dict) and isinstance(correct_data, dict):
                # Both are dicts, use key lookup
                for q_num, answer in answers_data.items():
                    if q_num in correct_data:
                        correct_answer = correct_data[q_num]
                        if isinstance(correct_answer, list):
                            if answer in correct_answer:
                                correct_count += 1
                        else:
                            if answer == correct_answer:
                                correct_count += 1
            else:
                # Fallback for other formats
                raise ValueError(f"Incompatible data types: answers={type(answers_data)}, correct={type(correct_data)}")
            
            score = f"{correct_count}/{total_questions}"
            percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            data.append({
                'ID': sub_id,
                'User ID': user_id,
                'Full Name': fullname or 'Unknown',
                'Username': username or 'None',
                'Exam': title or 'Unknown',
                'Exam ID': exam_id,
                'Date (UTC+5)': local_date,
                'Deadline (UTC+5)': local_deadline,
                'Late Submission': is_late,
                'Score': score,
                'Percentage': f"{percentage:.1f}%",
                'Answers': str(answers_data),
                'Correct': str(correct_data),
            })
        except Exception as e:
            # Log error for debugging
            logger.error(f"Error processing submission {sub_id} for export: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Handle parsing errors by including the error in the export
            data.append({
                'ID': sub_id,
                'User ID': user_id,
                'Full Name': fullname or 'Unknown',
                'Username': username or 'None',
                'Exam': title or 'Unknown',
                'Exam ID': exam_id,
                'Date (UTC+5)': local_date,
                'Deadline (UTC+5)': local_deadline,
                'Late Submission': is_late,
                'Score': 'Error',
                'Percentage': 'Error',
                'Answers': f"Error: {str(e)}",
                'Correct': 'N/A',
            })
    
    # Create DataFrame and export to Excel
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Submissions')
    
    # Prepare the file for sending
    output.seek(0)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    # Send the file
    await callback.message.answer_document(
        types.BufferedInputFile(
            output.getvalue(),
            filename=f"submissions_export_{now}.xlsx"
        ),
        caption="📊 Here is your exported submissions data."
    )

@reser.callback_query(CbData("stats_back"), statsstates.export_select)
async def back_to_stats_from_export_select(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_back"), statsstates.select_user_export)
async def back_to_stats_from_user_export(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_back"), statsstates.select_exam_export)
async def back_to_stats_from_exam_export(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_back"), statsstates.viewing_all)
async def back_to_stats_from_all_view(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_back"), statsstates.viewing_by_user)
async def back_to_stats_from_user_view(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_back"), statsstates.viewing_by_exam)
async def back_to_stats_from_exam_view(callback: types.CallbackQuery, state: FSMContext):
    await back_to_stats_menu(callback, state)

@reser.callback_query(CbData("stats_export_select"))
async def select_export_type(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📊 <b>Export to Excel</b>\n\n"
        "Select what data you would like to export:",
        reply_markup=export_select_menu
    )
    await state.set_state(statsstates.export_select)
    await callback.answer()

@reser.callback_query(CbData("stats_export_all"), statsstates.export_select)
async def export_all_excel(callback: types.CallbackQuery, state: FSMContext):
    await export_excel(callback, state, export_type="all")

@reser.callback_query(CbData("stats_export_by_user"), statsstates.export_select)
async def select_user_for_export(callback: types.CallbackQuery, state: FSMContext):
    # Get users who have submissions
    all_users = db.fetchall("""
        SELECT DISTINCT u.idx, u.userid, u.fullname, u.username FROM users u
        JOIN submissions s ON u.userid = s.userid
        ORDER BY u.fullname
    """)
    
    if not all_users:
        await callback.answer("No users with submissions found.")
        return
    
    # Setup pagination for users
    users_per_page = config.USERS_PER_PAGE
    total_pages = (len(all_users) + users_per_page - 1) // users_per_page
    page = 1
    
    # Store pagination info in state - FIXED: include export_prefix in state
    await state.update_data(
        all_users=all_users,
        users_page=page,
        users_total_pages=total_pages,
        users_per_page=users_per_page,
        export_mode=True,
        export_prefix="export_user_"  # Store the prefix in state
    )
    
    await show_users_export_page(callback, state)
    await state.set_state(statsstates.select_user_export)

async def show_users_export_page(callback, state):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    users_per_page = data.get('users_per_page', config.USERS_PER_PAGE)
    all_users = data.get('all_users', [])
    export_prefix = data.get('export_prefix', "export_user_")  # FIXED: get prefix from state
    
    # Calculate start and end indices for slicing
    start_idx = (page - 1) * users_per_page
    end_idx = min(start_idx + users_per_page, len(all_users))
    
    # Get users for current page
    current_page_users = all_users[start_idx:end_idx]
    
    if not current_page_users:
        await callback.answer("No users found for this page.")
        return
    
    await callback.message.edit_text(
        f"👤 <b>Select a user to export submissions:</b> (Page: {page} of {total_pages})",
        reply_markup=user_selection_kb(current_page_users, page, total_pages, export_prefix=export_prefix)
    )

@reser.callback_query(CbData("users_prev_page"), statsstates.select_user_export)
async def users_export_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    
    if page > 1:
        await state.update_data(users_page=page-1)
        await show_users_export_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("users_next_page"), statsstates.select_user_export)
async def users_export_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    
    if page < total_pages:
        await state.update_data(users_page=page+1)
        await show_users_export_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("users_jump_page_"), statsstates.select_user_export)
async def users_export_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total_pages = data.get('users_total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(users_page=target_page)
    await show_users_export_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbData("stats_export_by_exam"), statsstates.export_select)
async def select_exam_for_export(callback: types.CallbackQuery, state: FSMContext):
    # Get exams with submissions
    all_exams = db.fetchall("""
        SELECT DISTINCT e.idx, e.title FROM exams e
        JOIN submissions s ON e.idx = s.exid
        ORDER BY e.title
    """)
    
    if not all_exams:
        await callback.answer("No exams with submissions found.")
        return
    
    # Setup pagination for exams
    exams_per_page = config.EXAMS_PER_PAGE
    total_pages = (len(all_exams) + exams_per_page - 1) // exams_per_page
    page = 1
    
    # Store pagination info in state - FIXED: include export_prefix in state
    await state.update_data(
        all_exams=all_exams,
        exams_page=page,
        exams_total_pages=total_pages,
        exams_per_page=exams_per_page,
        export_mode=True,
        export_prefix="export_exam_"  # Store the prefix in state
    )
    
    await show_exams_export_page(callback, state)
    await state.set_state(statsstates.select_exam_export)

async def show_exams_export_page(callback, state):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    exams_per_page = data.get('exams_per_page', config.EXAMS_PER_PAGE)
    all_exams = data.get('all_exams', [])
    export_prefix = data.get('export_prefix', "export_exam_")  # FIXED: get prefix from state
    
    # Calculate start and end indices for slicing
    start_idx = (page - 1) * exams_per_page
    end_idx = min(start_idx + exams_per_page, len(all_exams))
    
    # Get exams for current page
    current_page_exams = all_exams[start_idx:end_idx]
    
    if not current_page_exams:
        await callback.answer("No exams found for this page.")
        return
    
    await callback.message.edit_text(
        f"📚 <b>Select an exam to export submissions:</b> (Page: {page} of {total_pages})",
        reply_markup=exam_selection_kb(current_page_exams, page, total_pages, export_prefix=export_prefix)
    )

@reser.callback_query(CbData("exams_prev_page"), statsstates.select_exam_export)
async def exams_export_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    
    if page > 1:
        await state.update_data(exams_page=page-1)
        await show_exams_export_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("exams_next_page"), statsstates.select_exam_export)
async def exams_export_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    
    if page < total_pages:
        await state.update_data(exams_page=page+1)
        await show_exams_export_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("exams_jump_page_"), statsstates.select_exam_export)
async def exams_export_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total_pages = data.get('exams_total_pages', 1)
    
    # Extract target page from callback data
    target_page = int(callback.data.split("_")[-1])
    
    # Check if trying to jump before page 1
    if target_page < 1:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Check if trying to jump past the last page
    if target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    
    # Ensure the target page is within valid range
    await state.update_data(exams_page=target_page)
    await show_exams_export_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbDataStartsWith("export_user_"), statsstates.select_user_export)
async def export_user_submissions(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Extract ID directly from callback data to handle potential format variations
        user_id = callback.data.split("_")[2]
        logger.info(f"Exporting user with user_id: {user_id}")
        await export_excel(callback, state, export_type="by_user", user_id=user_id)
    except Exception as e:
        logger.error(f"Error exporting user submissions: {str(e)}")
        logger.error(traceback.format_exc())
        await callback.answer("Error processing export. Please try again.", show_alert=True)

@reser.callback_query(CbDataStartsWith("export_exam_"), statsstates.select_exam_export)
async def export_exam_submissions(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Extract ID directly from callback data to handle potential format variations
        exam_id = callback.data.split("_")[2]
        logger.info(f"Exporting exam with exam_id: {exam_id}")
        await export_excel(callback, state, export_type="by_exam", exam_id=exam_id)
    except Exception as e:
        logger.error(f"Error exporting exam submissions: {str(e)}")
        logger.error(traceback.format_exc())
        await callback.answer("Error processing export. Please try again.", show_alert=True)

async def export_excel(callback, state, export_type="all", user_id=None, exam_id=None):
    await callback.answer("Preparing Excel file...")
    msg = await callback.message.edit_text("Preparing Excel file...\nThis may take a while.")
    # Build query based on export type
    query = """
        SELECT s.idx, u.fullname, u.username, e.title, s.date, s.answers, e.correct, u.userid, e.idx, e.sdate
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
    """
    
    params = []
    if export_type == "by_user" and user_id:
        query += " WHERE s.userid = %s"
        params.append(user_id)
    elif export_type == "by_exam" and exam_id:
        query += " WHERE s.exid = %s"
        params.append(exam_id)
    
    query += " ORDER BY s.date DESC"
    
    # Get submissions based on query
    submissions = db.fetchall(query, tuple(params))
    
    if not submissions:
        await msg.edit_text("Couldn't found any submissions to export.")
        return
    
    # Prepare data for Excel
    data = []
    for sub in submissions:
        sub_id, fullname, username, title, date, answers, correct, user_id, exam_id, deadline = sub
        
        # Convert dates to UTC+5 for display in Excel
        local_date = format_datetime(date)
        local_deadline = format_datetime(deadline) if deadline else 'None'
        
        # Check if submission was late
        is_late = "No"
        if deadline and date > deadline:
            is_late = "Yes"
        
        # Handle different data formats for answers and correct answers
        try:
            # Log data for debugging
            logger.info(f"Processing export for submission {sub_id}")
            
            if not answers or not correct:
                raise ValueError("Empty answer or correct data")
                
            answers_data = json.loads(answers if answers else "{}")
            correct_json = json.loads(correct if correct else "{}")
            
            # Check if answers are nested in a dict with 'answers' key
            # Use built-in dict type instead of the imported dict module
            if isinstance(correct_json, dict) and 'answers' in correct_json:
                correct_data = correct_json['answers']
            else:
                correct_data = correct_json
            
            # Calculate score based on data type
            correct_count = 0
            total_questions = len(correct_data) if correct_data else 0
            
            if total_questions == 0:
                raise ValueError("No questions in correct data")
            
            # Handle different data structures using same approach as in users/results.py
            if isinstance(answers_data, dict) and isinstance(correct_data, list):
                # Convert dict to list if correct_data is list
                answers_list = []
                for i in range(1, len(correct_data) + 1):
                    q_num = str(i)
                    answers_list.append(answers_data.get(q_num, ""))
                
                for i, (answer, correct_answer) in enumerate(zip(answers_list, correct_data)):
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, list) and isinstance(correct_data, list):
                # Both are lists, use direct comparison
                for i, answer in enumerate(answers_data):
                    if i >= len(correct_data):
                        continue
                    correct_answer = correct_data[i]
                    if isinstance(correct_answer, list):
                        if answer in correct_answer:
                            correct_count += 1
                    else:
                        if answer == correct_answer:
                            correct_count += 1
            elif isinstance(answers_data, dict) and isinstance(correct_data, dict):
                # Both are dicts, use key lookup
                for q_num, answer in answers_data.items():
                    if q_num in correct_data:
                        correct_answer = correct_data[q_num]
                        if isinstance(correct_answer, list):
                            if answer in correct_answer:
                                correct_count += 1
                        else:
                            if answer == correct_answer:
                                correct_count += 1
            else:
                # Fallback for other formats
                raise ValueError(f"Incompatible data types: answers={type(answers_data)}, correct={type(correct_data)}")
            
            score = f"{correct_count}/{total_questions}"
            percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            data.append({
                'ID': sub_id,
                'User ID': user_id,
                'Full Name': fullname or 'Unknown',
                'Username': username or 'None',
                'Exam': title or 'Unknown',
                'Exam ID': exam_id,
                'Date (UTC+5)': local_date,
                'Deadline (UTC+5)': local_deadline,
                'Late Submission': is_late,
                'Score': score,
                'Percentage': f"{percentage:.1f}%",
                'Answers': str(answers_data),
                'Correct': str(correct_data),
            })
        except Exception as e:
            # Log error for debugging
            logger.error(f"Error processing submission {sub_id} for export: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Handle parsing errors by including the error in the export
            data.append({
                'ID': sub_id,
                'User ID': user_id,
                'Full Name': fullname or 'Unknown',
                'Username': username or 'None',
                'Exam': title or 'Unknown',
                'Exam ID': exam_id,
                'Date (UTC+5)': local_date,
                'Deadline (UTC+5)': local_deadline,
                'Late Submission': is_late,
                'Score': 'Error',
                'Percentage': 'Error',
                'Answers': f"Error: {str(e)}",
                'Correct': 'N/A',
            })
    
    # Create DataFrame and export to Excel
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Submissions')
    
    # Prepare the file for sending
    output.seek(0)
    
    # Create filename with export type info
    filename_prefix = "all_submissions"
    if export_type == "by_user":
        user_name = db.fetchone("SELECT fullname FROM users WHERE userid = %s", (user_id,))
        if user_name:
            filename_prefix = f"user_{user_name[0]}"
    elif export_type == "by_exam":
        exam_name = db.fetchone("SELECT title FROM exams WHERE idx = %s", (exam_id,))
        if exam_name:
            filename_prefix = f"exam_{exam_name[0]}"
    
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{filename_prefix}_{now}.xlsx"
    
    # Send the file
    await msg.answer_document(
        types.BufferedInputFile(
            output.getvalue(),
            filename=filename
        ),
        caption=f"📊 Excel export: {filename_prefix.replace('_', ' ')}"
    )
    await msg.delete()
    # Return to statistics menu
    await back_to_stats_menu(callback, state, new_msg=True)

@reser.callback_query(CbData("stats_back"))
async def back_to_stats_menu(callback: types.CallbackQuery, state: FSMContext, new_msg=False):
    # Reset state data
    await state.clear()
    
    msg = None
    if new_msg:
        msg = await callback.message.answer("📊 <b>Bot Statistics</b>\n\nLoading...")
    else:
        msg = await callback.message.edit_text("📊 <b>Bot Statistics</b>\n\nLoading...")

    # Get basic statistics again
    total_users = db.fetchone("SELECT COUNT(*) FROM users")[0]
    total_submissions = db.fetchone("SELECT COUNT(*) FROM submissions")[0]
    active_exams = db.fetchone("SELECT COUNT(*) FROM exams WHERE sdate > NOW()")[0]
    
    # Get recent submissions (last 5)
    recent_subs = db.fetchall("""
        SELECT s.idx, u.fullname, e.title, s.date 
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        ORDER BY s.date DESC LIMIT 5
    """)
    
    # Format the statistics message
    stats_message = f"📊 <b>Bot Statistics</b>\n\n"
    stats_message += f"👥 <b>Total Users:</b> {total_users}\n"
    stats_message += f"📝 <b>Total Submissions:</b> {total_submissions}\n"
    stats_message += f"⚡️ <b>Active Exams:</b> {active_exams}\n\n"
    
    stats_message += f"🕒 <b>Recent Submissions:</b>\n"
    subs = ""
    if recent_subs:
        for idx, sub in enumerate(recent_subs, 1):
            subs += f"{idx}. {html.bold(sub[1])} - {html.italic(sub[2])}: {sub[3].strftime('%Y-%m-%d %H:%M')}\n"
    else:
        subs = "No recent submissions.\n"
    stats_message += html.blockquote(subs)
    await msg.edit_text(stats_message, reply_markup=stats_menu)
    await state.set_state(statsstates.stmenu)
    await callback.answer()

# ...existing code...
@reser.callback_query(CbData("export_users_prev_page"), statsstates.select_user_export)
async def export_users_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    if page > 1:
        await state.update_data(users_page=page-1)
        await show_users_export_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("export_users_next_page"), statsstates.select_user_export)
async def export_users_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('users_page', 1)
    total_pages = data.get('users_total_pages', 1)
    if page < total_pages:
        await state.update_data(users_page=page+1)
        await show_users_export_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("export_users_jump_page_"), statsstates.select_user_export)
async def export_users_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total_pages = data.get('users_total_pages', 1)
    target_page = int(callback.data.split("_")[-1])
    if target_page < 1 or target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    await state.update_data(users_page=target_page)
    await show_users_export_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")

@reser.callback_query(CbData("export_exams_prev_page"), statsstates.select_exam_export)
async def export_exams_prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    if page > 1:
        await state.update_data(exams_page=page-1)
        await show_exams_export_page(callback, state)
    else:
        await callback.answer("You are already on the first page", show_alert=True)

@reser.callback_query(CbData("export_exams_next_page"), statsstates.select_exam_export)
async def export_exams_next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('exams_page', 1)
    total_pages = data.get('exams_total_pages', 1)
    if page < total_pages:
        await state.update_data(exams_page=page+1)
        await show_exams_export_page(callback, state)
    else:
        await callback.answer("You are already on the last page", show_alert=True)

@reser.callback_query(CbDataStartsWith("export_exams_jump_page_"), statsstates.select_exam_export)
async def export_exams_jump_to_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total_pages = data.get('exams_total_pages', 1)
    target_page = int(callback.data.split("_")[-1])
    if target_page < 1 or target_page > total_pages:
        await callback.answer("Can't jump to that page", show_alert=True)
        return
    await state.update_data(exams_page=target_page)
    await show_exams_export_page(callback, state)
    await callback.answer(f"Jumped to page {target_page}")
