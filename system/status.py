import os
import time
import psutil
import shutil
import platform
from bot import Bot
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config


_uptime = time.time()
pid = os.getpid()
proc = psutil.Process(pid)


def format_uptime(seconds: float) -> str:
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{days:.0f}d")
    if hours:
        parts.append(f"{hours:.0f}h")
    if minutes:
        parts.append(f"{minutes:.0f}m")
    if seconds or not parts:
        parts.append(f"{seconds:.0f}s")

    return " ".join(parts)


@Bot.on_message(Config.IS_ADMIN & filters.command("status"))
async def status(_, message: Message):
    now = time.time()

    bot_uptime = format_uptime(now - _uptime)
    system_uptime = format_uptime(now - psutil.boot_time())

    disk = shutil.disk_usage("/")

    await message.reply(
        "**Bot Status**:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Bot Uptime:", callback_data="None"),
                    InlineKeyboardButton(bot_uptime, callback_data="None"),
                ],
                [
                    InlineKeyboardButton(
                        "System Uptime:", callback_data="None"
                    ),
                    InlineKeyboardButton(system_uptime, callback_data="None"),
                ],
                [
                    InlineKeyboardButton(
                        "Memory Usage:", callback_data="None"
                    ),
                    InlineKeyboardButton(
                        f"{proc.memory_info().rss / 1024 ** 2:.2f} MB",
                        callback_data="None",
                    ),
                ],
                [
                    InlineKeyboardButton("Disk Usage", callback_data="None"),
                    InlineKeyboardButton(
                        f"{disk.used / 1024**3:.2f}/"
                        f"{disk.total / 1024**3:.2f} GB",
                        callback_data="None",
                    ),
                ],
                [
                    InlineKeyboardButton("Python", callback_data="None"),
                    InlineKeyboardButton(
                        platform.python_version(), callback_data="None"
                    ),
                ],
            ]
        ),
    )


__all__ = ["status"]
__plugin__ = True
