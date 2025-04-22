import copy
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
ydl_opts = {
    "quiet": True,
    "proxy": Config.PROXY,
    "cookies": Config.getdata("youtube_cookies_file")
}


@Client.on_message(
    Config.IS_ADMIN
    & filters.regex(fr"^{Config.REGEX_CMD_PREFIXES}youtube {yt_regex}$")
)
async def youtube_message(_: Client, message: Message):
    vid_id = message.matches[0].group("id")
    keyboard = []
    formats = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(yt_url.format(vid_id), download=False)
        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            text = "**ERROR**: " + str(e)
            if "Sign in" in text:
                text += (
                    "\nSet your cookie file via: "
                    "`{}setdata {} youtube_cookies_file"
                    " [path to the cookies file]`"
                    "\n(Preferably put the cookies file in the data folder)"
                ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])

            await message.reply(text)
            return
        time = datetime.timedelta(seconds=int(info["duration"]))

        for format in info.get("formats", []):
            if (
                not format["ext"] == "mp4" or not format.get("format_note")
                or format["audio_ext"] != "none"
            ):
                continue

            if not format["format_note"] in formats:
                formats.append(format["format_note"])
                size_bytes = format.get(
                    "filesize",
                    format.get("filesize_approx", 0)
                )
                size_mb = (
                    size_bytes / (1024 * 1024)
                    if size_bytes
                    else "Unknown"
                )
                keyboard.append([InlineKeyboardButton(
                    f"{format['format_note']} ({size_mb:.2f} MB)",
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
    parameters = copy.deepcopy(ydl_opts)
    parameters.update({
        "format": quality,
        "outtmpl": download_path + youtube_file_name,
    })
    await query.answer("Download is in process")
    msg = await query.message.reply("Downloading the video.")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yt_url.format(vid_id)])
        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            text = "**ERROR**: " + str(e)
            if "Sign in" in text:
                text += (
                    "\nSet your cookie file via: "
                    "`{}setdata {} youtube_cookies_file"
                    " [path to the cookies file]`"
                    "\n(Preferably put the cookies file in the data folder)"
                ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])

            await msg.edit(text)
            return
    await msg.edit("Download is done.")


__all__ = ["youtube_message", "youtube_callback"]
__plugin__ = True
