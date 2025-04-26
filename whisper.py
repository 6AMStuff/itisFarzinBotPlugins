from pyrogram import Client
from pyrogram.types import InlineQuery, CallbackQuery


@Client.on_inline_query()
async def whisper_inline(_: Client, query: InlineQuery):
    pass


@Client.on_callback_query()
async def whisper_callback(_: Client, query: CallbackQuery):
    pass


__all__ = ["whisper_inline", "whisper_callback"]
__plugin__ = True
