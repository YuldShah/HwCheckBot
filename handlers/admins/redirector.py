from aiogram import Router, types, F, html
from data import config
from filters import IsAdmin, IsAdminCallback, CbData, CbDataStartsWith


redirector = Router()
redirector.message.filter(IsAdmin())
redirector.callback_query.filter(IsAdminCallback())

