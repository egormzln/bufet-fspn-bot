from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers import main_handler
import main
from handlers.flood_handler import flood_handler

router = Router(name='posting_handlers')


class PushPostFSM(StatesGroup):
    waiting_post = State()


@router.message(StateFilter(None), Command("push_post"))
async def push_post_start_handler(msg: Message, state: FSMContext):
    if not main.admin_check(msg.from_user.id):
        await flood_handler.flood_handler(msg)
        return

    await msg.answer("Отправь мне пост для рассылки 📬")
    await state.set_state(PushPostFSM.waiting_post)


@router.message(PushPostFSM.waiting_post)
async def push_post_waiting_handler(msg: Message, state: FSMContext):
    if not main.admin_check(msg.from_user.id):
        await flood_handler.flood_handler(msg)
        return

    post_photo_id = msg.photo[-1].file_id if len(msg.photo) >= 0 else None
    post_text = None

    if msg.text is not None:
        post_text = msg.text
    elif msg.caption is not None:
        post_text = msg.caption

    await state.update_data(post_photo_id=post_photo_id, post_text=post_text)

    keyboard = InlineKeyboardBuilder()
    button1 = InlineKeyboardButton(callback_data="push_post_admins", text="Тест для админов")
    button2 = InlineKeyboardButton(callback_data="push_post_users", text="Отправить юзерам")
    keyboard.row(button1, button2)

    if post_photo_id is not None:
        await state.update_data(post_type="photo")

        await main.bot.send_photo(
            chat_id=msg.chat.id,
            photo=post_photo_id,
            caption=post_text,
            reply_markup=keyboard.as_markup()
        )
    else:
        await state.update_data(post_type="text")

        await msg.answer(
            text=post_text,
            reply_markup=keyboard.as_markup()
        )


@router.callback_query(F.data.startswith('push_post_'))
async def push_post_sending_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()

    push_target = call.data.split("_")[-1]
    post_data = await state.get_data()

    match push_target:
        case "admins":
            main.logger.info("Admins broadcast...")
            await test_post_for_admins(call, post_data)
        case "users":
            main.logger.info("Users broadcast...")
            await broadcast_users(call, post_data)


async def broadcast_users(call: CallbackQuery, post_data):
    users = await get_all_users()

    user_counter = 0

    for user in users:
        main.logger.info(f"[{user_counter}] Broadcast {user["username"]} {user["chat_id"]}")

        if post_data["post_type"] == "photo":
            await main.bot.send_photo(
                chat_id=user["chat_id"],
                photo=post_data["post_photo_id"],
                caption=post_data["post_text"],
            )
        elif post_data["post_type"] == "text":
            await main.bot.send_message(
                chat_id=user["chat_id"],
                text=post_data["post_text"],
            )
        user_counter += 1


async def test_post_for_admins(call: CallbackQuery, post_data):
    for admin in main.admin_users.items():
        if post_data["post_type"] == "photo":
            await main.bot.send_photo(
                chat_id=admin[1],
                photo=post_data["post_photo_id"],
                caption=post_data["post_text"],
            )
        elif post_data["post_type"] == "text":
            await call.answer(
                text=post_data["post_text"],
            )


async def get_all_users():
    users = []
    async for user in main.users_collection.find({}):
        users.append(user)
    return users
