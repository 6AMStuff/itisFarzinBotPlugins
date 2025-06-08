import time
from bot import Bot
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config


_uptime = time.time()


@Bot.on_message(Config.IS_ADMIN & filters.command("status"))
async def status(_, message: Message):
    now = time.time()
    seconds = now - _uptime
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    uptime = []
    if days:
        uptime.append(f"{days:.0f}d")
    if hours:
        uptime.append(f"{hours:.0f}h")
    if minutes:
        uptime.append(f"{minutes:.0f}m")
    if seconds or not uptime:
        uptime.append(f"{seconds:.0f}s")

    await message.reply(
        "**Bot Status**:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Uptime:", callback_data="None"),
                    InlineKeyboardButton(
                        " ".join(uptime), callback_data="None"
                    ),
                ]
            ]
        ),
    )


__all__ = ["status"]
__plugin__ = True
