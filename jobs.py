import asyncio
from datetime import timedelta
from loader import db, bot

async def process_scheduled_tasks():
    """Fetch and execute scheduled tasks from PostgreSQL (using UTC+5)."""
    tasks = db.get_due_tasks()

    for task in tasks:
        task_id, user_id, task_name, task_data, run_at, created_at, completed = task

        # Convert run_at back to UTC+5 for display
        run_at_utc5 = run_at + timedelta(hours=5)

        try:
            if task_name == "send_reminder":
                await bot.send_message(user_id, f"Reminder: Your task was scheduled for {run_at_utc5} UTC+5!")

            db.mark_task_completed(task_id)  # Mark as completed

        except Exception as e:
            print(f"Error executing task {task_id}: {e}")

if __name__ == "__main__":
    asyncio.run(process_scheduled_tasks())
