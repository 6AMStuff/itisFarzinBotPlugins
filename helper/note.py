from pyrogram import Client
from pyrogram.types import Message

from config import Config


@Client.on_message(Config.IS_ADMIN)
async def note_message(_: Client, message: Message):
    pass


__all__ = ["note_message"]
__plugin__ = True
