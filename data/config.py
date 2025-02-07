import os

BOT_TOKEN = "8147677803:AAGklnHV8O0H29v9w_xlgBCnIudM9-VVUt4" #os.getenv("API_TOKEN")
ADMINS = [6520664733] # [int(x) for x in os.getenv("ADMINS").split()]
DB_URL = os.getenv("DATABASE_URL")
ADMIN_URL = "https://t.me/ekbekasatullayev"
# DB_URI =  "mongodb+srv://notyuldshah:<Description_56>@prproj.xbst3.mongodb.net/?retryWrites=true&w=majority&appName=prproj" #os.getenv("URI")
MAX_EXAMS_AT_A_TIME = 5
MULTIPLE_CHOICE_DEF = 4
MAX_QUESTION_IN_A_PAGE = 15
bot_info = None