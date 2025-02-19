from .admins import *
from .users import *
from .not_handled import remover

def register_handlers(dp):
    dp.include_routers(admin, reger, user, reshow, pub, allow, chhw, usrarch, test, stater, access, arch, set, nosub, remover)