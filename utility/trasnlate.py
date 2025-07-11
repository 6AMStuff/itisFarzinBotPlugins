from bot import Bot
from pyrogram import filters
from pyrogram.types import Message
from googletrans import Translator

from settings import Settings


translator = Translator()


@Bot.on_message(
    Settings.IS_ADMIN & filters.command("translate", Settings.CMD_PREFIXES)
)
async def translate(_: Bot, message: Message):
    action = message.command[0]
    if len(message.command) < 2:
        await message.reply(
            f"{Settings.CMD_PREFIXES[0]}{action} [language]"
            " *reply to a message"
        )
        return

    msg = message.reply_to_message
    if not msg:
        await message.reply("Reply to a message.")
        return

    language = message.command[1]
    text = msg.text or msg.caption
    try:
        result = await translator.translate(text, dest=language)
        await message.reply(
            text=f"From {result.src} to {result.dest}:\n{result.text}"
        )
    except Exception as e:
        await message.reply("*ERROR**: " + str(e))


__all__ = ["translate"]
__plugin__ = True
__bot_only__ = False
