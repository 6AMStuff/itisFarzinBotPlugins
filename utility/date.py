from bot import Bot
from pyrogram import filters
from datetime import datetime
from pyrogram.types import Message
from jdatetime import datetime as jdatetime

from settings import Settings


@Bot.on_message(filters.command("date", Settings.CMD_PREFIXES))
async def date(_: Bot, message: Message):
    today = datetime.today().astimezone(Settings.TIMEZONE)
    await message.reply(
        today.strftime("Date: %A, %B %d (%m/%d/%Y)\nTime: %H:%M:%S (%Z)")
    )


@Bot.on_message(filters.command("jdate", Settings.CMD_PREFIXES))
async def jdate(_: Bot, message: Message):
    today = jdatetime.today().astimezone(Settings.TIMEZONE)
    await message.reply(
        today.strftime("Date: %A, %B %d (%d/%m/%Y)\nTime: %H:%M:%S (%Z)")
    )


__all__ = ("date", "jdate")
__plugin__ = True
__bot_only__ = False
