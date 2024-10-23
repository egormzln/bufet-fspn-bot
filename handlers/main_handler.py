from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers import flood_handler
from main import admin_users, bot, users_collection, logger, admin_check

router = Router(name='main_handlers')

command_list = {
    "start": "Начало работы",
    "admin_list": "Список админов",
    "push_post": "Отправка поста",
}

# @formatter:off
base_msgs = {
    "hello": {
        "admin":
"""
Привет @{{username}}!\nТы админ этого бота!

Список команд:
{{command_list}}

Приветственное сообщение для пользователей:
""",
        "user":
            "Привет! Чтобы сделать заказ в нашем буфете нажми на кнопку «Сделать заказ»"
    },
    "order":
"""
Привет! Захотел перекусить между парами? 

Выбери из меню понравившееся блюдо 👇🏼
""",
    "order_create" : "Отличный выбор! Оплата прошла через студенческий билет",
    "flood": "Ой-ой, похоже, такое мы не сможем приготовить, выбери что-то из меню 😉",
}
# @formatter:on

keyboards = {
    "get_order": {
        "get_order_0": "Сделать заказ 🥐",
    },
    "create_order": {
        "create_order_0": "Колллоквиум с пепперони",
        "create_order_1": "Победные тосты",
        "create_order_2": "Эликсир счастья",
        "create_order_3": "Сытная сессия",
        "create_order_4": "Секретное блюдо",
    }
}

photo_ids = {
    "hello_img": "AgACAgIAAxkBAAIBU2cXjtoR8h_nRQ7NIhrLB9A0NFzUAAJs2jEbF_jASEnegEN2UbXWAQADAgADeQADNgQ",
    "get_order_img": "AgACAgIAAxkBAAIBVGcXjtoPikhE2S9DLq5jXyKITAIlAAJt2jEbF_jASBDzoRwskLLgAQADAgADeQADNgQ",
    "order_create_img": "AgACAgIAAxkBAAIBVWcXjtondpnfeEg4eYnEnN189C3XAAJu2jEbF_jASGeMd0SQAi5TAQADAgADeQADNgQ",
}


@router.message(CommandStart())
async def start_handler(msg: Message):
    await _save_user_info(msg)

    if admin_check(msg.from_user.id):
        msg_command_list = "\n".join([f"/{key} - {value}" for key, value in command_list.items()])
        await msg.answer(
            base_msgs["hello"]["admin"]
            .replace("{{username}}", msg.from_user.username)
            .replace("{{user_hello}}", base_msgs["hello"]["user"])
            .replace("{{command_list}}", msg_command_list),
        )
        # await user_hello(msg, disable_keyboard=True)
        await _user_hello_msg(msg)
    else:
        await _user_hello_msg(msg)


async def _user_hello_msg(msg: Message, disable_keyboard: bool = False):
    keyboard = InlineKeyboardBuilder()

    for el in keyboards["get_order"].items():
        button = InlineKeyboardButton(callback_data=el[0], text=el[1])
        keyboard.row(button)

    async with ChatActionSender(bot=bot, chat_id=msg.from_user.id, action="typing"):
        await bot.send_photo(
            chat_id=msg.chat.id,
            photo=photo_ids["hello_img"],
            caption=base_msgs["hello"]["user"],
            reply_markup=keyboard.as_markup(resize_keyboard=True) if not disable_keyboard else None
        )


async def _save_user_info(msg: Message):
    user_data = {
        "tg_id": msg.from_user.id,
        "chat_id": msg.chat.id,
        "username": msg.from_user.username if msg.from_user.last_name is not None else "",
        "first_name": msg.from_user.first_name,
        "last_name": msg.from_user.last_name if msg.from_user.last_name is not None else "",
        "date": str(datetime.now())
    }

    user = (msg.from_user.username, msg.from_user.id)

    if await users_collection.find_one({'tg_id': msg.from_user.id}) is None:
        try:
            await users_collection.insert_one(user_data)
            logger.info(f'Пользоваель @{user[0]} {user[1]} сохранён!')
        except:
            logger.info(f'Ошибка при добавлении пользователя @{user[0]} {user[1]} в БД')
    else:
        logger.info(f'Пользователь @{user[0]} {user[1]} уже есть в базе данных')


@router.callback_query(F.data.startswith('get_order'))
async def get_order_callback_query(call: CallbackQuery):
    await call.answer()

    keyboard = InlineKeyboardBuilder()

    for el in keyboards["create_order"].items():
        button = InlineKeyboardButton(callback_data=el[0], text=el[1])
        keyboard.row(button)

    async with ChatActionSender(bot=bot, chat_id=call.message.from_user.id, action="typing"):
        await bot.edit_message_media(
            media=InputMediaPhoto(media=photo_ids["get_order_img"]),
            message_id=call.message.message_id,
            chat_id=call.message.chat.id,
        )
        await bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=base_msgs["order"],
            reply_markup=keyboard.as_markup()
        )


@router.callback_query(F.data.startswith('create_order_'))
async def get_order_callback_query(call: CallbackQuery):
    await call.answer()

    async with ChatActionSender(bot=bot, chat_id=call.from_user.id, action="typing"):
        await bot.edit_message_media(
            media=InputMediaPhoto(media=photo_ids["order_create_img"]),
            message_id=call.message.message_id,
            chat_id=call.message.chat.id,
        )

        await bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=base_msgs["order_create"],
        )


@router.message(Command("admin_list"))
async def admin_list_handler(msg: Message):
    if admin_check(msg.from_user.id):
        msg_admin_list = "\n".join(f"@{_}" for _ in admin_users)
        await msg.reply(f"Вот список админов:\n{msg_admin_list}")
    else:
        await flood_handler.flood_handler(msg)
