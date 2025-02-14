from .admins import *
from .users import *
from .not_handled import remover

def register_handlers(dp):
    dp.include_routers(admin, user, reshow, pub, allow, chhw, test, stater, access, arch, set, nosub, reger, remover)