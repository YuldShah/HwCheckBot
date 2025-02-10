from utils.db import DatabaseManager
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from data import config

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def get_info(bot):
    config.bot_info = await bot.get_me()

dp = Dispatcher()

db = DatabaseManager(config.DB_URL)