import asyncio
from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.serialization import deserialize_telegram_object_to_python

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

    post_photo_id = None
    post_text = None

    if msg.photo is not None and len(msg.photo) >= 0:
        post_photo_id = msg.photo[-1].file_id

    if msg.text is not None:
        post_text = msg.text
    elif msg.caption is not None:
        post_text = msg.caption

    await state.update_data(post_photo_id=post_photo_id, post_text=post_text)

    keyboard = InlineKeyboardBuilder()
    button1 = InlineKeyboardButton(callback_data="push_post_admins", text="Тест для админов")
    button2 = InlineKeyboardButton(callback_data="push_post_users", text="Отправить юзерам")
    button3 = InlineKeyboardButton(callback_data="push_post_cancel", text="Отмена")
    keyboard.row(button1, button2)
    keyboard.row(button3)

    print(msg.entities)

    if post_photo_id is not None:
        await state.update_data(post_type="photo")

        await main.bot.send_photo(
            chat_id=msg.chat.id,
            photo=post_photo_id,
            caption=post_text,
            reply_markup=keyboard.as_markup(),
            caption_entities=msg.caption_entities
        )
    else:
        await state.update_data(post_type="text")

        await msg.answer(
            text=post_text,
            entities=msg.entities,
            reply_markup=keyboard.as_markup(),
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
            await state.clear()
            await main.bot.send_message(chat_id=call.message.chat.id, text="Отправка звершена")
        case "users":
            main.logger.info("Users broadcast...")
            await broadcast_users(call, post_data)
            await state.clear()
            await main.bot.send_message(chat_id=call.message.chat.id, text="Отправка звершена")
        case "cancel":
            await state.clear()
            await main.bot.send_message(chat_id=call.message.chat.id, text="Отправка отменена")

    await call.message.delete()


async def broadcast_users(call: CallbackQuery, post_data):
    users = await get_all_users()

    user_counter = 0

    notified_users = []

    for user in users:
        if user["chat_id"] not in notified_users:
            try:
                if post_data["post_type"] == "photo":
                    await main.bot.send_photo(
                        chat_id=user["chat_id"],
                        photo=post_data["post_photo_id"],
                        caption=post_data["post_text"],
                        caption_entities=call.message.caption_entities
                    )
                elif post_data["post_type"] == "text":
                    await main.bot.send_message(
                        chat_id=user["chat_id"],
                        text=post_data["post_text"],
                        entities=call.message.entities,
                        disable_web_page_preview=True
                    )
                try:
                    main.logger.info(f'[{user_counter}] Successfully notified @{user["username"]} {user["chat_id"]}')
                except:
                    print(f'[{user_counter}] Successfully notified')
            except:
                print(f'[{user_counter}] Bot blocked for {user["chat_id"]}')
            await asyncio.sleep(1)
        else:
            print(f'[{user_counter}] Already notified {user["chat_id"]}')
        user_counter += 1


async def test_post_for_admins(call: CallbackQuery, post_data):
    for admin in main.admin_users.items():
        if post_data["post_type"] == "photo":
            await main.bot.send_photo(
                chat_id=admin[1],
                photo=post_data["post_photo_id"],
                caption=post_data["post_text"],
                caption_entities=call.message.caption_entities
            )
        elif post_data["post_type"] == "text":
            await main.bot.send_message(
                chat_id=admin[1],
                text=post_data["post_text"],
                entities=call.message.entities,
                disable_web_page_preview=True
            )
        main.logger.info(f'Successfully notified @{admin[0]} {admin[1]}')


async def get_all_users():
    users = []
    async for user in main.users_collection.find({}):
        users.append(user)
    return users
