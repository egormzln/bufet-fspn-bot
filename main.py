import asyncio
import logging
import sys

from aiogram.client.default import DefaultBotProperties
from config import load_config
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
import motor.motor_asyncio

from handlers import main_handler, flood_handler, posting_hanndler

logger = logging.getLogger(__name__)

config = load_config()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties())

admin_users = {
    "egormzln": 720106691,
}

try:
    db_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongo_uri)
    bot_db = db_client["bufet_fspn"]
    users_collection = bot_db["users"]
except:
    print('No database')


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s',
        stream=sys.stdout
    )
    logger.info('Starting Bot...')

    try:
        await users_collection.create_index('tg_id', unique=True)
    except:
        logger.info('No database')

    dp = Dispatcher()
    dp.include_routers(
        main_handler.router,
        posting_hanndler.router,
        flood_handler.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def admin_check(user_id: int):
    return user_id in admin_users.values()


if __name__ == "__main__":
    asyncio.run(main())
