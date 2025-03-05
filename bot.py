import logging
import sys
from dotenv import load_dotenv
load_dotenv()
from loader import dp, db, bot, get_info
import asyncio
from data import config
from handlers import register_handlers

async def on_startup():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await get_info(bot)
    
    register_handlers(dp)
    db.create_tables()
    logging.warning("Database started...")

async def on_shutdown():
    logging.warning("Shutting down..")
    await dp.storage.close()
    logging.warning("Bot down")

async def main():
    await on_startup()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await on_shutdown()



if __name__ == '__main__':
    asyncio.run(main())