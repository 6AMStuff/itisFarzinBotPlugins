from bot import Bot
from pyrogram import filters
from pyrogram.types import Message

from config import Config


emoji_list = {
    "dice": "🎲",
    "dart": "🎯",
    "basketball": "🏀",
    "football": "⚽️",
    "bowling": "🎳",
    "slot": "🎰",
}


@Bot.on_message(
    Config.IS_ADMIN & filters.command("throw", Config.CMD_PREFIXES)
)
async def throw(app: Bot, message: Message):
    emoji = message.command[1] if len(message.command) > 1 else None
    if emoji not in emoji_list.values() and emoji not in emoji_list.keys():
        await message.reply(
            "The emoji should be one of the following: "
            + ", ".join(map(lambda emoji: f"`{emoji}`", emoji_list.values()))
            + "."
        )
        return

    await app.send_dice(
        message.chat.id, emoji_list[emoji] if emoji in emoji_list else emoji
    )


@Bot.on_message(
    Config.IS_ADMIN & filters.command("dice", Config.CMD_PREFIXES)
)
async def dice(app: Bot, message: Message):
    await app.send_dice(message.chat.id, emoji_list[message.command[0]])


@Bot.on_message(
    Config.IS_ADMIN & filters.command("dart", Config.CMD_PREFIXES)
)
async def dart(app: Bot, message: Message):
    await app.send_dice(message.chat.id, emoji_list[message.command[0]])


@Bot.on_message(
    Config.IS_ADMIN & filters.command("basketball", Config.CMD_PREFIXES)
)
async def basketball(app: Bot, message: Message):
    await app.send_dice(message.chat.id, emoji_list[message.command[0]])


@Bot.on_message(
    Config.IS_ADMIN & filters.command("bowling", Config.CMD_PREFIXES)
)
async def bowling(app: Bot, message: Message):
    await app.send_dice(message.chat.id, emoji_list[message.command[0]])


@Bot.on_message(
    Config.IS_ADMIN & filters.command("slot", Config.CMD_PREFIXES)
)
async def slot(app: Bot, message: Message):
    await app.send_dice(message.chat.id, emoji_list[message.command[0]])


__all__ = ["throw"]
__plugin__ = True
__bot_only__ = False
