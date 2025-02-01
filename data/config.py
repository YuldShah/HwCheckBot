import os

BOT_TOKEN = os.getenv("API_TOKEN")
ADMINS = [int(x) for x in os.getenv("ADMINS").split()]
DB_URI = os.getenv("URI")
MAX_EXAMS_AT_A_TIME = 5
MULTIPLE_CHOICE_DEF = 4
MAX_QUESTION_IN_A_PAGE = 15
bot_info = None