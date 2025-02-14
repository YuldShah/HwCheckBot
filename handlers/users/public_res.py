from aiogram import Router, F, types, html
from data import dict
from loader import db



pub = Router()


@pub.inline_query(F.query.startswith("sub_"))
async def search_results(query: types.InlineQuery):
    sub_code = query.query.split("_")[1]
    sub = db.fetchone("SELECT * FROM submissions WHERE random = %s", (sub_code,))
    if not sub:
        