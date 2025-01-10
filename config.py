import os

from dataclasses import dataclass


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    mongo_uri: str


def load_config() -> Config:
    run_in_docker = bool(os.getenv("RUN_IN_DOCKER"))
    bot_token = os.getenv("BOT_TOKEN")
    bot_instance = TgBot(token=bot_token)

    mongo_host = "localhost"
    if run_in_docker:
        mongo_host = os.getenv("MONGO_HOST")

    mongo_uri = (f"mongodb://{os.getenv("MONGO_INITDB_ROOT_USERNAME")}"
                 f":{os.getenv("MONGO_INITDB_ROOT_PASSWORD")}"
                 f"@{mongo_host}"
                 f":{os.getenv("MONGO_INITDB_ROOT_PORT")}")

    return Config(
        tg_bot=bot_instance,
        mongo_uri=mongo_uri
    )
