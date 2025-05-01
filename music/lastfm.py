import pylast
import urllib.parse
from pyrogram import Client, filters, errors
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChosenInlineResult, InlineKeyboardMarkup, InlineKeyboardButton,
    LinkPreviewOptions, CallbackQuery, InputMediaPhoto
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
            "`{0}setdata {1} lastfm_login_password [your_password_in_md5]`\n"
            "For converting your password to md5 hash:\n"
            "`python -c 'import hashlib; print(hashlib.md5(\"your password\""
            ".encode()).hexdigest())'`"
        ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])

    try:
        return pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=login_username,
            password_hash=password,
        )
    except Exception as e:
        return f"**ERROR**: {e}"


async def lastfm_status(
    app: Client,
    message_id: str,
    with_cover: bool = False,
    expanded: bool = False
):
    if isinstance(lastfm, str):
        await app.edit_inline_text(message_id, lastfm)
        return

    user = lastfm.get_user(USERNAME)
    now_playing = user.get_now_playing()
    recent_tracks = user.get_recent_tracks(limit=1)
    if not now_playing and len(recent_tracks) == 0:
        await app.edit_inline_text(message_id, "No track found.")
        return
    track = now_playing or recent_tracks[0].track
    text = (
        "{} {} listening to"
        "\n**{}** - [{}](https://www.last.fm/search/tracks?q={})"
    ).format(
        user.name,
        "is now" if bool(now_playing) else "was",
        track.artist,
        track.get_name(),
        urllib.parse.quote(str(track)),
    )
    if expanded:
        number = 0
        for played_track in user.get_recent_tracks(limit=4):
            recent_track = played_track.track
            if recent_track == track or number == 3:
                continue

            text += (
                "\n**{}** - [{}](https://www.last.fm/search/tracks?q={})"
            ).format(
                recent_track.artist,
                recent_track.get_name(),
                urllib.parse.quote(str(recent_track)),
            )
            number += 1

    buttons = []
    if not with_cover:
        buttons.append(
            InlineKeyboardButton(
                "🖼",
                "lastfm status {}with_cover".format(
                    "expanded_" if expanded else ""
                )
            )
        )
    buttons.append(
        InlineKeyboardButton("🔄", "lastfm status {}with{}_cover".format(
            "expanded_" if expanded else "",
            "" if with_cover else "out"
        ))
    )

    if expanded:
        buttons.append(
            InlineKeyboardButton("➖", "lastfm status with{}_cover".format(
                "" if with_cover else "out"
            ))
        )
    else:
        buttons.append(
            InlineKeyboardButton(
                "➕",
                "lastfm status expanded_with{}_cover".format(
                    "" if with_cover else "out"
                )
            )
        )

    try:
        if with_cover:
            await app.edit_inline_media(
                message_id,
                InputMediaPhoto(
                    track.get_cover_image(),
                    caption=text
                ),
                reply_markup=InlineKeyboardMarkup([buttons])
            )
        else:
            await app.edit_inline_text(
                message_id,
                text,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=InlineKeyboardMarkup([buttons])
            )
    except errors.exceptions.bad_request_400.MessageNotModified:
        pass
    except Exception as e:
        raise e


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
            await lastfm_status(app, chosen.inline_message_id)


@Client.on_callback_query(
    filters.regex(r"^lastfm (?P<action>\w+) (?P<mode>\w+)$")
)
async def lastfm_callback(app: Client, query: CallbackQuery):
    action, mode = query.matches[0].groups()

    if action == "status":
        match mode:
            case "with_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=True
                )
            case "without_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=False
                )
            case "expanded_with_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=True,
                    expanded=True
                )
            case "expanded_without_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=False,
                    expanded=True
                )


__all__ = ["lastfm_inline", "lastfm_inline_result", "lastfm_callback"]
__plugin__ = True
