from .admins import *
from .users import *
from .not_handled import remover

def register_handlers(dp):
    dp.include_routers(redirector, admin, allow, set, reger, user, remover)