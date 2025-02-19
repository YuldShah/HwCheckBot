from aiogram import Router, F, html, types
from filters import IsUser, IsSubscriber, IsUserCallback, IsSubscriberCallback, IsArchiveAllowed, IsArchiveAllowedCallback
from data import dict



usrarch = Router()
usrarch.message.filter(IsUser(), IsSubscriber(), IsArchiveAllowed())
usrarch.callback_query.filter(IsUserCallback(), IsSubscriberCallback(), IsArchiveAllowedCallback())

@usrarch.message(F.text == dict.archive)
async def archive(message: types.Message):
    