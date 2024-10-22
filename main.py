import asyncio
import logging
import sys

from aiogram.client.default import DefaultBotProperties
from config import load_config
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from handlers import main_handlers
import motor.motor_asyncio

logger = logging.getLogger(__name__)

admin_users = {
    # <username>: <id>
    "egormzln": 720106691,
    "katesproduction": 881225912,
    "mlnmql": 1436567716
}

config = load_config()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

main_router = Router(name='main_handlers')

# MONGO_USER = os.getenv('MONGO_INITDB_ROOT_USERNAME')
# MONGO_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
# MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
#
# # MongoDB connection URI
# mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@mongodb:27017/{MONGO_DB_NAME}"

try:
    db_client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
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
    dp.include_router(main_handlers.main_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
