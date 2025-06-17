import os
import time
import psutil
import shutil
import platform
from bot import Bot
from pyrogram import filters, raw
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
async def status(app: Bot, message: Message):
    now = time.time()

    uptime = getattr(app, "uptime", _uptime)
    bot_uptime = format_uptime(now - uptime)
    system_uptime = format_uptime(now - psutil.boot_time())
    await app.invoke(
        raw.functions.ping.Ping(ping_id=app.rnd_id()),
    )
    ping = round((time.time() - now) * 1000.0, 3)

    disk = shutil.disk_usage("/")
    uname = platform.uname()
    battery = psutil.sensors_battery()

    data = {
        "Bot Uptime:": bot_uptime,
        "System Uptime:": system_uptime,
        "Memory Usage:": f"{proc.memory_info().rss / 1024 ** 2:.2f} MB",
        "Battery Percentage:": f"{battery.percent}%" if battery else None,
        "Ping:": f"{ping} ms",
        "Disk Usage:": (
            f"{disk.used / 1024**3:.2f} / {disk.total / 1024**3:.2f} GB"
        ),
        "Python:": platform.python_version(),
        "OS:": f"{uname.system} {uname.release}",
    }

    await message.reply(
        "**Bot Status**:",
        reply_markup=InlineKeyboardMarkup(
            [
                InlineKeyboardButton(key, callback_data="None"),
                InlineKeyboardButton(str(value), callback_data="None"),
            ]
            for key, value in data.items()
            if value is not None
        ),
    )


__all__ = ["status"]
__plugin__ = True
