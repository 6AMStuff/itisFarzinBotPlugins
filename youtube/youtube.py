from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import Config


yt_regex = (
    r'(https?://)?(www\.|m\.)?(youtube|youtu)\.(com|be)/'
    r'(watch\?v=|embed/|v/|shorts/|)(?P<id>[a-zA-Z0-9_-]{11})'
)


@Client.on_message(
    Config.IS_ADMIN
    & filters.regex(fr"^{Config.REGEX_CMD_PREFIXES}youtube {yt_regex}$")
)
async def youtube_message(_: Client, message: Message):
    vid_id = message.matches[0].group("id")
    pass


@Client.on_callback_query(
    Config.IS_ADMIN
    & filters.regex(r"^youtube (?P<id>[a-zA-Z0-9_-]{11})(?: (?P<quality>\w+))$")
)
async def youtube_callback(_: Client, query: CallbackQuery):
    pass


__all__ = ["youtube_message", "youtube_callback"]
__plugin__ = True
