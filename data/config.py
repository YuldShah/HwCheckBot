import os

BOT_TOKEN = "8147677803:AAGklnHV8O0H29v9w_xlgBCnIudM9-VVUt4" #os.getenv("BOT_TOKEN")
ADMINS = [6520664733, 1428991138, 6888608063] # [int(x) for x in os.getenv("ADMINS").split()]
DB_URL =  "data/database.db" #"postgres://ud3vktgsm7c0kl:p2405e5f984cc0764f322f5f0fb190f6dee84f5a74e50c09d8579ebfba20143ec@cd27da2sn4hj7h.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d44dmdcte5vehd"
ADMIN_URL = "https://t.me/elbekasatullayev"
# DB_URI =  "mongodb+srv://notyuldshah:<Description_56>@prproj.xbst3.mongodb.net/?retryWrites=true&w=majority&appName=prproj" #os.getenv("URI")
MAX_EXAMS_AT_A_TIME = 5
MULTIPLE_CHOICE_DEF = 4
MAX_QUESTION_IN_A_PAGE = 15
bot_info = None