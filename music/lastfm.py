import pylast
import urllib.parse
from pyrogram import Client
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChosenInlineResult, InlineKeyboardMarkup, InlineKeyboardButton,
    LinkPreviewOptions
)

from config import Config


USERNAME = "itisFarzin"


def set_up_lastfm():
    global USERNAME
    api_key = Config.getdata("lastfm_api_key")
    api_secret = Config.getdata("lastfm_api_secret")
    login_username = Config.getdata("lastfm_login_username")
    USERNAME = str(Config.getdata("lastfm_username", login_username))
    password = Config.getdata("lastfm_login_password")
    if not all([api_key, api_secret, login_username, password]):
        return (
            "**ERROR**: Some data are missing.\n"
            "Set your Last.fm credentials via:\n"
            "`{0}setdata {1} lastfm_api_key [your_api_key]`\n"
            "`{0}setdata {1} lastfm_api_secret [your_api_secret]`\n"
            "`{0}setdata {1} lastfm_username [your_username]` (Optional)\n"
            "`{0}setdata {1} lastfm_login_username [your_username]`\n"
            "`{0}setdata {1} lastfm_login_password [your_password]`"
        ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])
    return pylast.LastFMNetwork(
        api_key=api_key,
        api_secret=api_secret,
        username=login_username,
        password_hash=pylast.md5(password),
    )


def on_data_change():
    global lastfm
    lastfm = set_up_lastfm()


lastfm = set_up_lastfm()


@Client.on_inline_query()
async def lastfm_inline(_: Client, query: InlineQuery):
    await query.answer(
        [
            InlineQueryResultArticle(
                title="LastFM Status",
                input_message_content=InputTextMessageContent("Status"),
                id="lastfm_status",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("LastFM Status", "None")]
                ])
            )
        ],
        cache_time=0
    )


@Client.on_chosen_inline_result()
async def lastfm_inline_result(app: Client, chosen: ChosenInlineResult):
    if isinstance(lastfm, str):
        await app.edit_inline_text(chosen.inline_message_id, lastfm)
        return

    match chosen.result_id:
        case "lastfm_status":
            user = lastfm.get_user(USERNAME)
            now_playing = user.get_now_playing()
            recent_tracks = user.get_recent_tracks(limit=1)
            if not now_playing and len(recent_tracks) == 0:
                await app.edit_inline_text(
                    chosen.inline_message_id,
                    "No track found."
                )
                return
            track = now_playing or recent_tracks[0].track
            text = (
                "{} {} listening to **{}** - [{}]"
                "(https://www.last.fm/search/tracks?q={})"
            ).format(
                user.name,
                "is now" if bool(now_playing) else "was",
                track.artist,
                track.get_name(),
                urllib.parse.quote(str(track)),
            )
            await app.edit_inline_text(
                chosen.inline_message_id,
                text,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )


__all__ = ["lastfm_inline", "lastfm_inline_result"]
__plugin__ = True
