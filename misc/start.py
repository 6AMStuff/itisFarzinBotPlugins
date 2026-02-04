from bot import Bot
from pyrogram import filters
from pyrogram.types import LinkPreviewOptions, Message

from bot.settings import Settings


@Bot.on_message(
    Settings.IS_ADMIN & filters.command("start", Settings.CMD_PREFIXES + ["/"])
)
async def start(_: Bot, message: Message):
    await message.reply(
        "Welcome to itisFarzin's personal assistant bot!"
        "\nYou can find the source code of me on [GitHub](https://github.com/6AMStuff/itisFarzinBot).",  # noqa: E501
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


__all__ = ("start",)
__plugin__ = True
__bot_only__ = False
