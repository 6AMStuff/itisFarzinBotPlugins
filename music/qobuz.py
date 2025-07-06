import os
import time
import httpx
import hashlib
import asyncio
from bot import Bot
from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from .util import (
    download_file,
    download_progress,
    parse_data,
    tag_file,
    error_handler,
    error_handler_decorator,
)

from config import Config


# Qobuz class from https://github.com/OrfiDev/orpheusdl-qobuz
# with some modifications
class Qobuz:
    def __init__(
        self,
        app_id: str | int,
        app_secret: str,
        auth_token: str,
        proxy: str = None,
    ):
        self.api_base = "https://www.qobuz.com/api.json/0.2/"
        self._app_id = str(app_id)
        self._app_secret = app_secret
        self._auth_token = auth_token
        self.session = httpx.AsyncClient(proxy=proxy)

    def headers(self) -> dict[str, str]:
        return {
            "X-Device-Platform": "android",
            "X-Device-Model": "Pixel 3",
            "X-Device-Os-Version": "10",
            "X-User-Auth-Token": self._auth_token,
            "X-Device-Manufacturer-Id": "482D8CB7-015D-402F-A93B-5EEF0E0996F3",
            "X-App-Version": "5.16.1.5",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build"
            + "/QP1A.190711.020) QobuzMobileAndroid/5.16.1.5-b21041415",
        }

    async def _get(self, url: str, params=None) -> dict:
        if not params:
            params = {}

        response = await self.session.get(
            self.api_base + url, params=params, headers=self.headers()
        )

        if response.status_code not in [200, 201, 202]:
            raise Exception(response.json()["message"])

        return response.json()

    async def check_token(self):
        params = {
            "app_id": self._app_id,
        }
        params["request_ts"], params["request_sig"] = self.create_signature(
            "user/get", params
        )

        response = await self._get("user/get", params)

        if not response["credential"]["parameters"]:
            raise Exception("Free accounts are not eligible for downloading")

    def create_signature(
        self, method: str, parameters: dict
    ) -> tuple[str, str]:
        timestamp = str(int(time.time()))
        to_hash = method.replace("/", "")

        for key in sorted(parameters.keys()):
            if key not in ["app_id", "user_auth_token"]:
                to_hash += key + parameters[key]

        to_hash += timestamp + self._app_secret
        signature = hashlib.md5(to_hash.encode()).hexdigest()
        return timestamp, signature

    async def search(
        self, query_type: str, query: str, offset: int = 0, limit: int = 10
    ) -> dict:
        return await self._get(
            "catalog/search",
            params={
                "query": query,
                "type": query_type + "s",
                "limit": limit,
                "offset": offset,
                "app_id": self._app_id,
            },
        )

    async def get_file_url(self, track_id: str, quality_id=27) -> dict:
        params = {
            "track_id": track_id,
            "format_id": str(quality_id),
            "intent": "stream",
            "sample": "false",
            "app_id": self._app_id,
            "user_auth_token": self._auth_token,
        }

        signature = self.create_signature("track/getFileUrl", params)
        params["request_ts"], params["request_sig"] = signature

        return await self._get("track/getFileUrl", params=params)

    async def get_track(self, track_id: str) -> dict:
        return await self._get(
            "track/get", params={"track_id": track_id, "app_id": self._app_id}
        )

    async def get_album(self, album_id: str) -> dict:
        return await self._get(
            "album/get",
            params={
                "album_id": album_id,
                "app_id": self._app_id,
                "extra": "albumsFromSameArtist,focusAll",
            },
        )


def set_up_qobuz():
    app_id = Config.getdata("qobuz_app_id")
    app_secret = Config.getdata("qobuz_app_secret")
    auth_token = Config.getdata("qobuz_auth_token")

    missing_data: list[str] = []
    if not app_id:
        missing_data.append("qobuz_app_id")
    if not app_secret:
        missing_data.append("qobuz_app_secret")
    if not auth_token or len(auth_token) == 0:
        missing_data.append("qobuz_auth_token")

    if missing_data:
        error_message = "**ERROR**: Missing data detected:\n"
        for item in missing_data:
            error_message += "`{}setdata {} {} [your_{}]`\n".format(
                Config.CMD_PREFIXES[0],
                __name__.split(".")[-1],
                item,
                item.replace("qobuz_", ""),
            )
        return error_message

    return Qobuz(app_id, app_secret, auth_token, Config.PROXY)


async def qobuz_search_keyboard(query: str, page: int = 0):
    keyboard = []
    result = await qobuz.search("track", query, offset=page * 10, limit=11)
    tracks = result["tracks"]["items"]

    if not tracks:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("No track was found.", "None")]]
        )

    for track in tracks[:10]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    parse_data("{time} | {name} - {artist}", track),
                    parse_data("qobuz trackinfo {id}", track),
                )
            ]
        )

    page_keyboard = []
    if page != 0:
        page_keyboard.append(
            InlineKeyboardButton("Previous Page", f"qose {query} {page-1}")
        )
    if len(tracks) == 11:
        page_keyboard.append(
            InlineKeyboardButton("Next Page", f"qose {query} {page+1}")
        )

    return InlineKeyboardMarkup(keyboard + [page_keyboard])


def on_data_change():
    global qobuz
    qobuz = set_up_qobuz()


qobuz = set_up_qobuz()


@Bot.on_message(
    Config.IS_ADMIN
    & filters.regex(
        rf"^{Config.REGEX_CMD_PREFIXES}qobuz"
        r"(?: https://www\.qobuz\.com/.*/album/.*/(?P<id>\w+)"
        r"| (?P<query>.+))?$"
    )
)
@error_handler_decorator
async def qobuz_message(_: Bot, message: Message):
    if isinstance(qobuz, str):
        await message.reply(qobuz)
        return

    album_id = message.matches[0].group("id")
    query = message.matches[0].group("query")

    if query:
        await message.reply(
            f"Results for **{query}**:",
            reply_markup=await qobuz_search_keyboard(query),
        )
        return
    elif not album_id:
        await message.reply(
            f"{Config.CMD_PREFIXES[0]}qobuz [album url] | [query to search]"
        )
        return

    try:
        album = await qobuz.get_album(album_id)
    except Exception as e:
        await message.reply("**ERROR**: " + str(e))
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "Download the album", f"qobuz dlalbum {album_id}"
            )
        ],
        [
            InlineKeyboardButton("—", "none"),
            InlineKeyboardButton("Tracks", "none"),
            InlineKeyboardButton("—", "none"),
        ],
    ]
    tracks = [
        [
            InlineKeyboardButton(
                parse_data("{time} | {name} - {artist}", track),
                parse_data("qobuz dltrack {id}", track),
            )
        ]
        for track in album["tracks"]["items"]
    ]
    await message.reply_photo(
        album["image"]["large"],
        caption=parse_data("{name} - {artist}", album),
        reply_markup=InlineKeyboardMarkup(keyboard + tracks),
    )


@Bot.on_callback_query(
    Config.IS_ADMIN & filters.regex(r"^qobuz (?P<type>\w+) (?P<id>\w+)$")
)
@error_handler_decorator
async def qobuz_callback(_: Bot, query: CallbackQuery):
    if isinstance(qobuz, str):
        await query.answer(qobuz)
        return

    loop = asyncio.get_running_loop()
    info = query.matches[0].groupdict()

    if info["type"] in ["dlalbum", "dltrack"]:
        try:
            await qobuz.check_token()
        except Exception as e:
            await query.answer("ERROR: " + str(e))
            return

        await query.answer("Download is in process.")
        download_path = (
            Config.getdata("download_path", "downloads", use_env=True) + "/"
        )

        if info["type"] == "dlalbum":
            album = await qobuz.get_album(info["id"])
            tracks = album["tracks"]["items"]
        else:
            _track = await qobuz.get_track(info["id"])
            album = await qobuz.get_album(_track["album"]["id"])
            tracks = [_track]

        _album_path = Config.getdata("qobuz_album_path", "{artist}/{name}")
        album_path = download_path + parse_data(_album_path, album) + "/"
        zfill = max(2, len(str(album["tracks_count"])))
        os.makedirs(album_path, exist_ok=True)

        cover_path = album_path + "cover.jpg"
        if not os.path.exists(cover_path):
            cover_url: str = album["image"]["large"].replace("600", "org")
            cover_msg = await query.message.reply("Downloading **cover.jpg**.")

            if await error_handler(
                download_file,
                kwargs=dict(
                    url=cover_url,
                    filename=cover_path,
                    proxy=Config.PROXY,
                    progress=download_progress,
                    progress_args=("cover.jpg", time.time(), cover_msg),
                ),
                update=cover_msg,
                text="Failed to download the cover.",
            ):
                if os.path.exists(cover_path):
                    os.remove(cover_path)

                return

            loop.call_later(5, lambda: asyncio.create_task(cover_msg.delete()))

        for track in tracks:
            stream_data = await qobuz.get_file_url(str(track["id"]))
            track.update(stream_data)
            track["track_number"] = str(track["track_number"]).zfill(zfill)
            track_msg = await query.message.reply(
                parse_data("Downloading **{name}**.", track)
            )
            _track_name = Config.getdata(
                "qobuz_track_name", "{track_number} {name}"
            )
            track_name = parse_data(_track_name + ".{format}", track)
            full_path = album_path + track_name
            if os.path.exists(full_path):
                await track_msg.edit(
                    parse_data("Track **{name}** already exists.", track)
                )
                loop.call_later(
                    5, lambda: asyncio.create_task(track_msg.delete())
                )
                continue

            if await error_handler(
                download_file,
                kwargs=dict(
                    url=stream_data["url"],
                    filename=full_path,
                    proxy=Config.PROXY,
                    progress=download_progress,
                    progress_args=(track_name, time.time(), track_msg),
                ),
                update=track_msg,
                text=parse_data(
                    "Failed to download the track **{name}**.", track
                ),
            ):
                if os.path.exists(full_path):
                    os.remove(full_path)

                continue

            track["source"] = "Qobuz"
            tag_file(full_path, cover_path, track)
            loop.call_later(5, lambda: asyncio.create_task(track_msg.delete()))

        await query.message.reply(
            parse_data(
                "Download of **{name}** by **{artist}** is complete.",
                album if info["type"] == "dlalbum" else tracks[0],
            )
        )
    elif info["type"] == "trackinfo":
        await query.answer()
        track = await qobuz.get_track(info["id"])
        album = await qobuz.get_album(track["album"]["id"])
        await query.message.reply_photo(
            album["image"]["large"],
            caption=parse_data("{name} - {artist}", track),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Download", parse_data("qobuz dltrack {id}", track)
                        )
                    ]
                ]
            ),
        )


@Bot.on_callback_query(
    Config.IS_ADMIN & filters.regex(r"^qose (?P<query>.+?) (?P<page>\d+)$")
)
@error_handler_decorator
async def qobuz_search(_: Bot, query: CallbackQuery):
    if isinstance(qobuz, str):
        await query.answer(qobuz)
        return

    search_query, page = query.matches[0].groups()
    await query.edit_message_reply_markup(
        await qobuz_search_keyboard(search_query, int(page))
    )


__all__ = ["qobuz_message", "qobuz_callback", "qobuz_search"]
__plugin__ = True
__bot_only__ = True
