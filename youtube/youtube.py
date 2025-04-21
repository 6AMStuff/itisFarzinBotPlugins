import yt_dlp
import datetime
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)

from config import Config


yt_regex = (
    r"(https?://)?(www\.|m\.)?(youtube|youtu)\.(com|be)/"
    r"(watch\?v=|embed/|v/|shorts/|)(?P<id>[a-zA-Z0-9_-]{11})"
)
yt_url = "https://www.youtube.com/watch?v={}"
resolutions = ["1080p", "720p", "480p", "360p", "144p"]


@Client.on_message(
    Config.IS_ADMIN
    & filters.regex(fr"^{Config.REGEX_CMD_PREFIXES}youtube {yt_regex}$")
)
async def youtube_message(_: Client, message: Message):
    vid_id = message.matches[0].group("id")
    ydl_opts = {
        "quiet": True,
        "proxy": Config.PROXY,
    }
    keyboard = []
    formats = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(yt_url.format(vid_id), download=False)
        time = datetime.timedelta(seconds=int(info["duration"]))

        for format in info.get("formats", []):
            if (
                not format["ext"] == "mp4" or not format.get("format_note")
                or format["audio_ext"] != "none"
            ):
                continue

            if not format["format_note"] in formats:
                formats.append(format["format_note"])
                keyboard.append([InlineKeyboardButton(
                    format["format_note"],
                    f"youtube {vid_id} {format['format_id']}"
                )])

        await message.reply_photo(
            info["thumbnail"],
            caption=f"Title: **{info['title']}**\n"
            + f"Duration: **{time}**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


@Client.on_callback_query(
    Config.IS_ADMIN
    & filters.regex(
        r"^youtube (?P<id>[a-zA-Z0-9_-]{11}) (?P<quality>\w+)$"
    )
)
async def youtube_callback(_: Client, query: CallbackQuery):
    vid_id, quality = query.matches[0].groups()
    download_path = Config.getdata(
        "download_path",
        "downloads",
        use_env=True
    ) + "/"
    youtube_file_name = Config.getdata(
        "youtube_file_name",
        "%(title)s.%(ext)s"
    )
    ydl_opts = {
        "format": quality,
        "outtmpl": download_path + youtube_file_name,
        "quiet": True,
        "proxy": Config.PROXY,
    }
    await query.answer("Download is in process")
    msg = await query.message.reply("Downloading the video.")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_url.format(vid_id)])
    await msg.edit("Download is done.")


__all__ = ["youtube_message", "youtube_callback"]
__plugin__ = True
