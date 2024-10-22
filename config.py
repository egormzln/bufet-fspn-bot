import os

from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    bot_instance = TgBot(token=bot_token)
    return Config(tg_bot=bot_instance)
