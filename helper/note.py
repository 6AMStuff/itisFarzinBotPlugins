from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config


@Client.on_message(
    Config.IS_ADMIN
    & filters.command(
        ["addnote", "getnote", "delnote", "notes"],
        Config.CMD_PREFIXES
    )
)
async def note_message(_: Client, message: Message):
    pass


__all__ = ["note_message"]
__plugin__ = True
