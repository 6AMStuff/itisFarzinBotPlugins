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
    Config.IS_ADMIN
    & filters.command(
        ["throw", "dice", "dart", "basketball", "bowling", "slot"],
        Config.CMD_PREFIXES
    )
)
async def throw(app: Bot, message: Message):
    emoji = message.command[0]
    if emoji == "throw":
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


__all__ = ["throw"]
__plugin__ = True
__bot_only__ = False
