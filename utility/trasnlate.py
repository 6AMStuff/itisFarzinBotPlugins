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
    text = None
    help = (
        f"{Settings.CMD_PREFIXES[0]}{action} [language]"
        " [text] / *reply to a message"
    )
    if len(message.command) < 2:
        await message.reply(help)
        return

    msg = message.reply_to_message
    if msg:
        text = msg.text or msg.caption
    elif len(message.command) > 2:
        text = " ".join(message.command[2:])

    if not text:
        await message.reply(help)
        return

    language = message.command[1]
    try:
        result = await translator.translate(text, dest=language)
        await message.reply(
            text="From **{}** to **{}**:\n`{}`".format(
                result.src.upper(), result.dest.upper(), result.text
            )
        )
    except Exception as e:
        await message.reply("*ERROR**: " + str(e))


__all__ = ["translate"]
__plugin__ = True
__bot_only__ = False
