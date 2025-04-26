import re
from pyrogram import Client, filters
from pyrogram.types import InlineQuery, CallbackQuery


@Client.on_inline_query(
    filters.regex(
        r"^(?P<sentence>.+?)\s+(?P<username>@[a-zA-Z_]{3,16})$",
        flags=re.DOTALL
    )
)
async def whisper_inline(_: Client, query: InlineQuery):
    sentence, username = query.matches[0].groups()


@Client.on_callback_query()
async def whisper_callback(_: Client, query: CallbackQuery):
    pass


__all__ = ["whisper_inline", "whisper_callback"]
__plugin__ = True
