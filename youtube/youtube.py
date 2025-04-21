from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import Config


@Client.on_message(Config.IS_ADMIN)
async def youtube_message(_: Client, message: Message):
    pass


@Client.on_callback_query(
    Config.IS_ADMIN
    & filters.regex(r"^youtube (?P<id>\w+)(?: (?P<quality>\w+))$")
)
async def youtube_callback(_: Client, query: CallbackQuery):
    pass


__all__ = ["youtube_message", "youtube_callback"]
__plugin__ = True
