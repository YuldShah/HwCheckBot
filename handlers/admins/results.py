from aiogram import types, Router, F, html
from data import dict as dict_labels  # Rename the import to avoid shadowing built-in dict
from keyboards.regular import main_key
from keyboards.inline.adm_inline import stats_menu, stats_pagination, user_selection_kb, exam_selection_kb, submission_details_kb, submission_detail_back_kb
from states import statsstates
from aiogram.fsm.context import FSMContext
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import logging
import traceback
from utils.db.storage import DatabaseManager
from data import config
from utils.yau import get_correct_text

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reser = Router()
reser.message.filter(IsAdmin())
reser.callback_query.filter(IsAdminCallback())

# Initialize database connection
db = DatabaseManager(config.DB_URL)

@reser.message(F.text == dict_labels.stats)
async def show_stats(message: types.Message, state: FSMContext):
    await message.answer(f"Menu {html.bold(f"{dict_labels.stats}")}", reply_markup=main_key)
    
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
    if recent_subs:
        for idx, sub in enumerate(recent_subs, 1):
            stats_message += f"{idx}. {html.bold(sub[1])} - {html.italic(sub[2])}: {sub[3].strftime('%Y-%m-%d %H:%M')}\n"
    else:
        stats_message += "No recent submissions.\n"
    
    await message.answer(stats_message, reply_markup=stats_menu)
    await state.set_state(statsstates.stmenu)

@reser.callback_query(CbData("stats_all"), statsstates.stmenu)
async def show_all_submissions(callback: types.CallbackQuery, state: FSMContext):
    # Get total count for pagination
    total_submissions = db.fetchone("SELECT COUNT(*) FROM submissions")[0]
    submissions_per_page = 10
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
        SELECT s.idx, u.fullname, e.title, s.date, s.answers, e.correct 
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
    message_text = f"📝 <b>Submissions (Page {page}/{total_pages})</b>\n\n"
    
    for idx, sub in enumerate(submissions, 1):
        sub_id, fullname, title, date, answers, correct = sub
        
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
            
            message_text += f"{offset + idx}. <b>{html.bold(fullname)}</b>\n"
            message_text += f"   📚 {html.bold(title or 'Unknown Test')}\n"
            message_text += f"   🕒 {date.strftime('%Y-%m-%d %H:%M')}\n"
            message_text += f"   ✅ Score: {score} ({percentage:.1f}%)\n"
            message_text += f"   <a href='details_{sub_id}'>👁 View Details</a>\n\n"
        
        except Exception as e:
            # Log the error with traceback for debugging
            logger.error(f"Error calculating score for submission {sub_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add a more descriptive error message in the UI
            message_text += f"{offset + idx}. <b>{html.bold(fullname or 'Unknown User')}</b>\n"
            message_text += f"   📚 {html.bold(title or 'Unknown Test')}\n"
            message_text += f"   🕒 {date.strftime('%Y-%m-%d %H:%M')}\n"
            message_text += f"   ❌ Error: Could not calculate score\n"
            message_text += f"   <a href='details_{sub_id}'>👁 View Details</a>\n\n"
    
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
    
    # Get submission details
    submission = db.fetchone("""
        SELECT s.idx, u.fullname, u.username, e.title, s.date, s.answers, e.correct 
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        WHERE s.idx = %s
    """, (sub_id,))
    
    if not submission:
        await callback.answer("Submission not found.")
        return
    
    sub_id, fullname, username, title, date, answers_json, correct_json = submission
    
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
                f"🕒 <b>Date:</b> {date.strftime('%Y-%m-%d %H:%M')}\n\n"
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
                f"🕒 <b>Date:</b> {date.strftime('%Y-%m-%d %H:%M')}\n\n"
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
                f"🕒 <b>Date:</b> {date.strftime('%Y-%m-%d %H:%M')}\n\n"
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
        details_text += f"🕒 <b>Date:</b> {date.strftime('%Y-%m-%d %H:%M')}\n\n"
        
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

@reser.callback_query(CbData("back_to_submissions"))
async def back_to_submissions_list(callback: types.CallbackQuery, state: FSMContext):
    await show_submissions_page(callback, state)
    await callback.answer()

@reser.callback_query(CbData("stats_prev_page"))
async def prev_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    
    if page > 1:
        await state.update_data(page=page-1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("Already on the first page")

@reser.callback_query(CbData("stats_next_page"))
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    total_pages = data.get('total_pages', 1)
    
    if page < total_pages:
        await state.update_data(page=page+1)
        await show_submissions_page(callback, state)
    else:
        await callback.answer("Already on the last page")

@reser.callback_query(CbData("stats_by_user"), statsstates.stmenu)
async def select_user(callback: types.CallbackQuery, state: FSMContext):
    # Get users who have submissions
    users = db.fetchall("""
        SELECT DISTINCT u.idx, u.userid, u.fullname, u.username FROM users u
        JOIN submissions s ON u.userid = s.userid
        ORDER BY u.fullname
    """)
    
    if not users:
        await callback.answer("No users with submissions found.")
        return
    
    await callback.message.edit_text(
        "👤 <b>Select a user to view their submissions:</b>",
        reply_markup=user_selection_kb(users)
    )
    
    await state.set_state(statsstates.select_user)
    await callback.answer()

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
    exams = db.fetchall("""
        SELECT DISTINCT e.idx, e.title FROM exams e
        JOIN submissions s ON e.idx = s.exid
        ORDER BY e.title
    """)
    
    if not exams:
        await callback.answer("No exams with submissions found.")
        return
    
    await callback.message.edit_text(
        "📚 <b>Select an exam to view submissions:</b>",
        reply_markup=exam_selection_kb(exams)
    )
    
    await state.set_state(statsstates.select_exam)
    await callback.answer()

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
    
    # Get all submissions with details
    submissions = db.fetchall("""
        SELECT s.idx, u.fullname, u.username, e.title, s.date, s.answers, e.correct, u.userid, e.idx
        FROM submissions s
        JOIN users u ON s.userid = u.userid
        JOIN exams e ON s.exid = e.idx
        ORDER BY s.date DESC
    """)
    
    if not submissions:
        await callback.message.answer("No submissions to export.")
        return
    
    # Prepare data for Excel
    data = []
    for sub in submissions:
        sub_id, fullname, username, title, date, answers, correct, user_id, exam_id = sub
        
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
                'Date': date,
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
                'Date': date,
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

@reser.callback_query(CbData("stats_back"))
async def back_to_stats_menu(callback: types.CallbackQuery, state: FSMContext):
    # Reset state data
    await state.clear()
    
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
    if recent_subs:
        for idx, sub in enumerate(recent_subs, 1):
            stats_message += f"{idx}. {html.bold(sub[1])} - {html.italic(sub[2])}: {sub[3].strftime('%Y-%m-%d %H:%M')}\n"
    else:
        stats_message += "No recent submissions.\n"
    
    await callback.message.edit_text(stats_message, reply_markup=stats_menu)
    await state.set_state(statsstates.stmenu)
    await callback.answer()
