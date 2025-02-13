import os

BOT_TOKEN = "8147677803:AAGklnHV8O0H29v9w_xlgBCnIudM9-VVUt4" #os.getenv("API_TOKEN")
ADMINS = [6520664733, 1428991138] # [int(x) for x in os.getenv("ADMINS").split()]
DB_URL = os.getenv("DATABASE_URL") #"postgres://u3iocbm9tkirb2:p4feedb440e4ea87a19da99c285a3335b5a2c65ab756624f1ce4cf1e018a33416@cd27da2sn4hj7h.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/degsa10e7nuinb" #
ADMIN_URL = "https://t.me/elbekasatullayev"
# DB_URI =  "mongodb+srv://notyuldshah:<Description_56>@prproj.xbst3.mongodb.net/?retryWrites=true&w=majority&appName=prproj" #os.getenv("URI")
MAX_EXAMS_AT_A_TIME = 5
MULTIPLE_CHOICE_DEF = 4
MAX_QUESTION_IN_A_PAGE = 15
bot_info = None