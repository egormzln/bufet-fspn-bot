from aiogram import Router
from aiogram.types import Message

from handlers import main_handler

router = Router(name='flood_handler')


# Flood handler
@router.message()
async def flood_handler(msg: Message):
    await msg.answer(main_handler.base_msgs["flood"])
