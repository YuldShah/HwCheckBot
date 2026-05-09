import asyncio
from datetime import timedelta
from loader import db, bot

async def process_scheduled_tasks():
    """Fetch and execute scheduled tasks from PostgreSQL (using UTC+5)."""
    tasks = db.get_due_tasks()

    for task in tasks:
        task_id, user_id, task_name, task_data, run_at, created_at, completed = task

        run_at_utc5 = run_at + timedelta(hours=5)

        try:
            if task_name == "send_reminder":
                await bot.send_message(user_id, f"Reminder: Your task was scheduled for {run_at_utc5} UTC+5!")

            elif task_name == "deadline_broadcast":
                exam_title = task_data or "a homework"
                users = db.fetchall("SELECT userid FROM users WHERE allowed >= 1") or []
                for (uid,) in users:
                    try:
                        await bot.send_message(
                            uid,
                            f"⏰ <b>Deadline Reminder!</b>\n\n"
                            f"The deadline for <b>{exam_title}</b> is in 1 hour!\n\n"
                            f"Please submit your work before the deadline."
                        )
                    except Exception:
                        pass  # User may have blocked the bot

            db.mark_task_completed(task_id)

        except Exception as e:
            print(f"Error executing task {task_id}: {e}")

if __name__ == "__main__":
    asyncio.run(process_scheduled_tasks())
