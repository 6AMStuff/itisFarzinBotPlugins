import qrcode
from bot import Bot
from io import BytesIO
from pyrogram import filters
from pyrogram.types import Message

from settings import Settings


def generate_qr(text: str) -> BytesIO:
    img = qrcode.make(text)
    bio = BytesIO()
    bio.name = "qr.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio


@Bot.on_message(
    Settings.IS_ADMIN & filters.command("qrcode", Settings.CMD_PREFIXES)
)
async def qrcode_message(_: Bot, message: Message):
    action = message.command[0]
    start_index = len(action) + 2
    text = message.text[start_index:]
    qr_image = generate_qr(text)
    await message.reply_photo(photo=qr_image, caption="Here's your QR code!")


__all__ = ["qrcode_message"]
__plugin__ = True
__bot_only__ = False
