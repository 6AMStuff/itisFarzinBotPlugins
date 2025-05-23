import pylast
import datetime
import humanize
import urllib.parse
from pyrogram import Client, filters, errors
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ChosenInlineResult,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LinkPreviewOptions,
    CallbackQuery,
    InputMediaPhoto,
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
    missing_data: list[str] = []

    if not api_key:
        missing_data.append("lastfm_api_key")
    if not api_secret:
        missing_data.append("lastfm_api_secret")
    if not login_username:
        missing_data.append("lastfm_login_username")
    if not password:
        missing_data.append("lastfm_login_password")

    if missing_data:
        error_message = "**ERROR**: Missing data detected:\n"
        for item in missing_data:
            error_message += "`{}setdata {} {} [your_{}]`\n".format(
                Config.CMD_PREFIXES[0],
                __name__.split(".")[-1],
                item,
                item.replace("lastfm_", ""),
            )

        if "lastfm_login_password" in missing_data:
            error_message += (
                "\nFor converting your password to md5 hash:\n"
                "`python -c 'import hashlib;"
                ' print(hashlib.md5("your password".encode()).hexdigest())\'`'
            )
        return error_message

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
    expanded: bool = False,
):
    if isinstance(lastfm, str):
        await app.edit_inline_text(message_id, lastfm)
        return

    user = lastfm.get_user(USERNAME)
    recent_tracks = user.get_recent_tracks(
        limit=4 if expanded else 1, now_playing=True
    )
    text = "{} {} listening to".format(
        user.name, "was" if recent_tracks[0].timestamp else "is now"
    )
    for played_track in recent_tracks:
        track = played_track.track
        time = (
            humanize.naturaltime(
                datetime.datetime.fromtimestamp(int(played_track.timestamp))
            )
            if str(played_track.timestamp).isdigit()
            else None
        )
        text += "\n**{}** - [{}]({}){}, {:,} plays".format(
            track.artist,
            track.get_name(),
            track.get_url(),
            f", {time}" if time else "",
            track.get_userplaycount(),
        )

    buttons = []
    if not with_cover:
        buttons.append(
            InlineKeyboardButton(
                "🖼",
                "lastfm status {}with_cover".format(
                    "expanded_" if expanded else ""
                ),
            )
        )

    buttons.append(
        InlineKeyboardButton(
            "🔄",
            "lastfm status {}with{}_cover".format(
                "expanded_" if expanded else "", "" if with_cover else "out"
            ),
        )
    )

    if expanded:
        buttons.append(
            InlineKeyboardButton(
                "➖",
                "lastfm status with{}_cover".format(
                    "" if with_cover else "out"
                ),
            )
        )
    else:
        buttons.append(
            InlineKeyboardButton(
                "➕",
                "lastfm status expanded_with{}_cover".format(
                    "" if with_cover else "out"
                ),
            )
        )

    try:
        cover = ""
        try:
            cover = recent_tracks[0].track.get_cover_image()
        except IndexError:
            with_cover = False
        if with_cover:
            await app.edit_inline_media(
                message_id,
                InputMediaPhoto(cover, text),
                reply_markup=InlineKeyboardMarkup([buttons]),
            )
        else:
            await app.edit_inline_text(
                message_id,
                text,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_markup=InlineKeyboardMarkup([buttons]),
            )
    except errors.exceptions.bad_request_400.MessageNotModified:
        pass
    except Exception as e:
        raise e


async def lastfm_top(app: Client, message_id: str, mode: str, time: str):
    if isinstance(lastfm, str):
        await app.edit_inline_text(message_id, lastfm)
        return

    user = lastfm.get_user(USERNAME)
    _time = {
        "1w": "7day",
        "1m": "1month",
        "3m": "3month",
        "6m": "6month",
        "1y": "12month",
        "alltime": "overall",
    }[time]
    time_text = {
        "1w": "1 Week",
        "1m": "1 Month",
        "3m": "3 Months",
        "6m": "6 Months",
        "1y": "1 Year",
        "alltime": "All Time",
    }[time]
    if mode == "artists":
        tops = user.get_top_artists(_time, 5)
    elif mode == "albums":
        tops = user.get_top_albums(_time, 5)
    else:
        tops = user.get_top_tracks(_time, 5)

    text = f"{user.name}'s Top {mode.title()} of the Last {time_text}:\n"
    if tops:
        for i, top in enumerate(tops, start=1):
            top.item.username = USERNAME  # Fixes user play count for artists
            text += (
                "\n{}. [{}](https://www.last.fm/search/tracks?q={}) ->"
                " {} plays"
            ).format(
                i,
                top.item,
                urllib.parse.quote(str(top.item)),
                top.item.get_userplaycount(),
            )
    else:
        text += "\nNothing were found."

    await app.edit_inline_text(
        message_id,
        text,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


def on_data_change():
    global lastfm
    lastfm = set_up_lastfm()


async def lastfm_chosen_filter(_, __, chosen: ChosenInlineResult):
    return chosen.result_id in ("lastfm_status", "lastfm_expanded_status")


lastfm = set_up_lastfm()
lastfm_chosen = filters.create(lastfm_chosen_filter)


@Client.on_inline_query(group=1)
async def lastfm_inline(_: Client, query: InlineQuery):
    await query.answer(
        [
            InlineQueryResultArticle(
                title="LastFM Status",
                input_message_content=InputTextMessageContent("Status"),
                id="lastfm_status",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("LastFM Status", "None")]]
                ),
            ),
            InlineQueryResultArticle(
                title="LastFM Expanded Status",
                input_message_content=InputTextMessageContent(
                    "Expanded status"
                ),
                id="lastfm_expanded_status",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("LastFM Status", "None")]]
                ),
            ),
            InlineQueryResultArticle(
                title="Top artists/albums/tracks",
                input_message_content=InputTextMessageContent("Choose type:"),
                id="top",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Artists", "lastfm top artists"
                            ),
                            InlineKeyboardButton(
                                "Albums", "lastfm top albums"
                            ),
                            InlineKeyboardButton(
                                "Tracks", "lastfm top tracks"
                            ),
                        ]
                    ]
                ),
            ),
        ],
        cache_time=0,
    )


@Client.on_chosen_inline_result(lastfm_chosen)
async def lastfm_inline_result(app: Client, chosen: ChosenInlineResult):
    if isinstance(lastfm, str):
        await app.edit_inline_text(chosen.inline_message_id, lastfm)
        return

    match chosen.result_id:
        case "lastfm_status":
            await lastfm_status(app, chosen.inline_message_id)
        case "lastfm_expanded_status":
            await lastfm_status(app, chosen.inline_message_id, expanded=True)


@Client.on_callback_query(
    filters.regex(r"^lastfm (?P<action>\w+) (?P<mode>\w+)(?: (?P<time>\w+))?$")
)
async def lastfm_callback(app: Client, query: CallbackQuery):
    action, mode, time = query.matches[0].groups()

    if action == "status":
        await query.answer("Wait.")
        match mode:
            case "with_cover":
                await lastfm_status(
                    app, query.inline_message_id, with_cover=True
                )
            case "without_cover":
                await lastfm_status(
                    app, query.inline_message_id, with_cover=False
                )
            case "expanded_with_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=True,
                    expanded=True,
                )
            case "expanded_without_cover":
                await lastfm_status(
                    app,
                    query.inline_message_id,
                    with_cover=False,
                    expanded=True,
                )
    elif action == "top":
        if not time:
            await query.edit_message_text(
                "Choose time period:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "1W", f"lastfm top {mode} 1w"
                            ),
                            InlineKeyboardButton(
                                "1M", f"lastfm top {mode} 1m"
                            ),
                            InlineKeyboardButton(
                                "3M", f"lastfm top {mode} 3m"
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                "6M", f"lastfm top {mode} 6m"
                            ),
                            InlineKeyboardButton(
                                "1Y", f"lastfm top {mode} 1y"
                            ),
                            InlineKeyboardButton(
                                "All time", f"lastfm top {mode} alltime"
                            ),
                        ],
                    ]
                ),
            )
            return
        await query.answer("Wait.")
        await lastfm_top(app, query.inline_message_id, mode, time)


__all__ = ["lastfm_inline", "lastfm_inline_result", "lastfm_callback"]
__plugin__ = True
