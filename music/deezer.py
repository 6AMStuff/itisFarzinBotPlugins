import os
import httpx
import hashlib
import asyncio
from bot import Bot
from time import time
from math import ceil
from random import randint
from typing import Optional
from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from cryptography.hazmat.backends import default_backend
from .util import (
    download_file,
    download_progress,
    parse_data,
    tag_file,
    error_handler,
    error_handler_decorator,
)
from cryptography.hazmat.decrepit.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher, modes

from config import Config


# Deezer classes from https://github.com/uhwot/orpheusdl-deezer
# with some modifications
class APIError(Exception):
    def __init__(self, type, msg, payload):
        self.type = type
        self.msg = msg
        self.payload = payload

    def __str__(self):
        return ", ".join((self.type, self.msg, str(self.payload)))


class DeezerAPI:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bf_secret: str,
        proxy: Optional[str] = None,
    ):
        self.gw_light_url = "https://www.deezer.com/ajax/gw-light.php"
        self.api_token = ""
        self.client_id = client_id
        self.client_secret = client_secret

        self.bf_secret = bf_secret.encode("ascii")

        self.session = httpx.AsyncClient(proxy=proxy)
        self.session.headers.update(
            {
                "accept": "*/*",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64)"
                + " AppleWebKit/537.36 (KHTML, like Gecko)"
                + " Chrome/96.0.4664.110 Safari/537.36",
                "content-type": "text/plain;charset=UTF-8",
                "origin": "https://www.deezer.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "same-origin",
                "sec-fetch-dest": "empty",
                "referer": "https://www.deezer.com/",
                "accept-language": "en-US,en;q=0.9",
            }
        )

    async def _api_call(self, method: str, payload: Optional[dict] = None):
        api_token = (
            self.api_token
            if method not in ("deezer.getUserData", "user.getArl")
            else ""
        )
        params = {
            "method": method,
            "input": 3,
            "api_version": 1.0,
            "api_token": api_token,
            "cid": randint(0, 1_000_000_000),
        }

        resp = (
            await self.session.post(
                self.gw_light_url, params=params, json=payload or {}
            )
        ).json()

        if resp["error"]:
            type = list(resp["error"].keys())[0]
            msg = list(resp["error"].values())[0]
            raise APIError(type, msg, resp["payload"])

        if method == "deezer.getUserData":
            self.api_token = resp["results"]["checkForm"]
            self.country = resp["results"]["COUNTRY"]
            self.license_token = resp["results"]["USER"]["OPTIONS"][
                "license_token"
            ]
            self.renew_timestamp = ceil(time())
            self.language = resp["results"]["USER"]["SETTING"]["global"][
                "language"
            ]

            self.available_formats = ["MP3_128"]
            format_dict = {"web_hq": "MP3_320", "web_lossless": "FLAC"}
            for k, v in format_dict.items():
                if resp["results"]["USER"]["OPTIONS"][k]:
                    self.available_formats.append(v)

        return resp["results"]

    async def login_via_email(self, email: str, password: str):
        # server sends set-cookie header with anonymous sid
        await self.session.get("https://www.deezer.com")

        password = hashlib.md5(password.encode()).hexdigest()

        params = {
            "app_id": self.client_id,
            "login": email,
            "password": password,
            "hash": hashlib.md5(
                (
                    self.client_id + email + password + self.client_secret
                ).encode()
            ).hexdigest(),
        }

        # server sends set-cookie header with account sid
        json = (
            await self.session.get(
                "https://connect.deezer.com/oauth/user_auth.php", params=params
            )
        ).json()

        if "error" in json:
            raise Exception(
                "Error while getting access token, check your credentials"
            )

        arl = await self._api_call("user.getArl")

        return arl, self.login_via_arl(arl)

    async def login_via_arl(self, arl: str):
        self.session.cookies.set("arl", arl, domain=".deezer.com")
        user_data = await self._api_call("deezer.getUserData")

        if not user_data["USER"]["USER_ID"]:
            self.session.cookies.clear()
            raise Exception("Invalid arl")

        return user_data

    async def get_track(self, id: str | int):
        return await self._api_call("deezer.pageTrack", {"sng_id": id})

    async def get_track_data(self, id: str | int):
        return await self._api_call("song.getData", {"sng_id": id})

    async def get_track_lyrics(self, id: str | int):
        return await self._api_call("song.getLyrics", {"sng_id": id})

    async def get_track_contributors(self, id: str | int):
        return (
            await self._api_call(
                "song.getData",
                {"sng_id": id, "array_default": ["SNG_CONTRIBUTORS"]},
            )
        )["SNG_CONTRIBUTORS"]

    async def get_track_cover(self, id: str | int):
        return (
            await self._api_call(
                "song.getData",
                {"sng_id": id, "array_default": ["ALB_PICTURE"]},
            )
        )["ALB_PICTURE"]

    async def get_track_data_by_isrc(self, isrc: str):
        resp = await self.session.get(
            f"https://api.deezer.com/track/isrc:{isrc}"
        ).json()
        if "error" in resp:
            raise Exception(resp["error"]["message"])

        return {
            "SNG_ID": resp["id"],
            "SNG_TITLE": resp["title_short"],
            "VERSION": resp["title_version"],
            "ARTISTS": [{"ART_NAME": a["name"]} for a in resp["contributors"]],
            "EXPLICIT_LYRICS": str(int(resp["explicit_lyrics"])),
            "ALB_TITLE": resp["album"]["title"],
        }

    async def get_album(self, id: str | int):
        try:
            return await self._api_call(
                "deezer.pageAlbum", {"alb_id": id, "lang": self.language}
            )
        except APIError as e:
            if e.payload:
                return await self._api_call(
                    "deezer.pageAlbum",
                    {
                        "alb_id": e.payload["FALLBACK"]["ALB_ID"],
                        "lang": self.language,
                    },
                )
            else:
                raise e

    async def get_playlist(self, id: str | int, nb: int, start: int):
        return await self._api_call(
            "deezer.pagePlaylist",
            {
                "nb": nb,
                "start": start,
                "playlist_id": id,
                "lang": self.language,
                "tab": 0,
                "tags": True,
                "header": True,
            },
        )

    async def get_artist_name(self, id: str | int):
        return (
            await self._api_call(
                "artist.getData", {"art_id": id, "array_default": ["ART_NAME"]}
            )
        )["ART_NAME"]

    async def search(self, query: str, type: str, start: int, nb: int):
        return await self._api_call(
            "search.music",
            {
                "query": query,
                "start": start,
                "nb": nb,
                "filter": "ALL",
                "output": type.upper(),
            },
        )

    async def get_artist_album_ids(
        self, id: str | int, start: int, nb: int, credited_albums: bool
    ):
        payload = {
            "art_id": id,
            "start": start,
            "nb": nb,
            "filter_role_id": [0, 5] if credited_albums else [0],
            "nb_songs": 0,
            "discography_mode": "all" if credited_albums else None,
            "array_default": ["ALB_ID"],
        }
        resp = await self._api_call("album.getDiscography", payload)
        return [a["ALB_ID"] for a in resp["data"]]

    async def get_track_url(
        self,
        id: str | int,
        track_token: str,
        track_token_expiry: str,
        format: str,
    ):
        # renews license token
        if time() - self.renew_timestamp >= 3600:
            await self._api_call("deezer.getUserData")

        # renews track token
        if time() - track_token_expiry >= 0:
            track_token = (
                await self._api_call(
                    "song.getData",
                    {"sng_id": id, "array_default": ["TRACK_TOKEN"]},
                )
            )["TRACK_TOKEN"]

        json = {
            "license_token": self.license_token,
            "media": [
                {
                    "type": "FULL",
                    "formats": [{"cipher": "BF_CBC_STRIPE", "format": format}],
                }
            ],
            "track_tokens": [track_token],
        }
        resp = (
            await self.session.post(
                "https://media.deezer.com/v1/get_url", json=json
            )
        ).json()
        return resp["data"][0]["media"][0]["sources"][0]["url"]

    def _get_blowfish_key(self, track_id: str | int):
        # yeah, you use the bytes of the hex digest of the hash. bruh moment
        md5_id = (
            hashlib.md5(str(track_id).encode()).hexdigest().encode("ascii")
        )

        key = bytes(
            [md5_id[i] ^ md5_id[i + 16] ^ self.bf_secret[i] for i in range(16)]
        )

        return key


class Deezer(DeezerAPI):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bf_secret: str,
        proxy: str = None,
    ):
        super().__init__(client_id, client_secret, bf_secret, proxy)

    @classmethod
    async def create(
        cls, client_id: str, client_secret: str, bf_secret: str, arl: str
    ):
        instance = cls(client_id, client_secret, bf_secret, Config.PROXY)
        await instance.login_via_arl(arl)
        return instance

    def _track(self, data: dict[str, str]):
        result = dict(
            id=data["SNG_ID"],
            title=data["SNG_TITLE"],
            version=data.get("VERSION"),
            artist={"name": data["ART_NAME"]},
            artists=[
                {"name": artist["ART_NAME"]} for artist in data["ARTISTS"]
            ],
            preview=next(
                (
                    item["HREF"]
                    for item in data["MEDIA"]
                    if item.get("TYPE") == "preview"
                ),
                None,
            ),
            time=data["SNG_ID"],
            duration=data["DURATION"],
            track_token=data["TRACK_TOKEN"],
            track_token_expire=data["TRACK_TOKEN_EXPIRE"],
            album_id=data["ALB_ID"],
            album_picture=data["ALB_PICTURE"],
            disc_number=data["DISK_NUMBER"],
            track_number=data["TRACK_NUMBER"],
            composer={
                "name": ", ".join(
                    (data["SNG_CONTRIBUTORS"] or {}).get("composer", [])
                )
            },
            copyright=data.get("COPYRIGHT"),
        )

        result["format"] = ""
        for _format in ["FLAC", "MP3_320", "MP3_128"]:
            if f"FILESIZE_{_format}" in data:
                format = data[f"FILESIZE_{_format}"]
                if format != "0":
                    result[_format.lower()] = data[f"FILESIZE_{_format}"]

                if not result["format"]:
                    result["format"] = _format.lower()

        return result

    def _cover(self, hash: str, resolution: int = 3000):
        resolution = 3000 if resolution > 3000 else resolution
        compression = 50

        return (
            f"https://cdn-images.dzcdn.net/images/cover/{hash}/"
            + f"{resolution}x0-000000-{compression}-0-0.jpg"
        )

    async def search_track(self, query: str, offset: int = 0, limit: int = 10):
        results = (await super().search(query, "track", offset, limit))["data"]
        return [self._track(result) for result in results]

    async def get_track(self, id: str | int):
        track = (await super().get_track(id))["DATA"]
        return self._track(track)

    async def get_track_cover(
        self,
        id: Optional[str | int] = None,
        track: Optional[dict[str, str]] = None,
        resolution: int = 3000,
    ):
        if not id and not track:
            return

        if id:
            cover_hash = await super().get_track_cover(id)
        else:
            cover_hash = track["album_picture"]

        return self._cover(cover_hash, resolution=resolution)

    async def get_track_lyrics(self, id):
        try:
            data = await super().get_track_lyrics(id)
        except Exception:
            return None

        lyrics = {}
        for lyric in data.get("LYRICS_SYNC_JSON", []):
            if "lrc_timestamp" in lyric:
                lyrics[lyric["lrc_timestamp"]] = lyric["line"]

        return lyrics

    async def get_album(self, id: str | int):
        album = await super().get_album(id)
        data = album["DATA"]
        return dict(
            id=data["ALB_ID"],
            title=data["ALB_TITLE"],
            artist={"name": data["ART_NAME"]},
            artists=[
                {"name": artist["ART_NAME"]} for artist in data["ARTISTS"]
            ],
            tracks_count=data["NUMBER_TRACK"],
            songs=(
                [self._track(track) for track in album["SONGS"]["data"]]
                if "SONGS" in album
                else []
            ),
            media_count="",
            release_date=data.get("ORIGINAL_RELEASE_DATE", ""),
            duration=data["DURATION"],
            cover=self._cover(data["ALB_PICTURE"]),
        )

    async def get_album_songs(
        self, id: str | int, start: int = 0, limit: int = 500
    ):
        return [
            self._track(track)
            for track in (
                await self._api_call(
                    "song.getListByAlbum",
                    {"alb_id": id, "start": start, "nb": limit},
                )
            )["data"]
        ]

    async def get_file_url(self, track: dict[str, str]):
        return await super().get_track_url(
            track["id"],
            track["track_token"],
            track["track_token_expire"],
            track["format"].upper(),
        )

    async def decrypt_chunk(self, index: int, chunk: str, id: str | int):
        bf_key = self._get_blowfish_key(id)
        cipher = Cipher(
            algorithms.Blowfish(bf_key),
            modes.CBC(b"\x00\x01\x02\x03\x04\x05\x06\x07"),
            backend=default_backend(),
        )
        if index % 3 == 0 and len(chunk) == 2048:
            decryptor = cipher.decryptor()
            chunk = decryptor.update(chunk) + decryptor.finalize()

        return chunk

    async def check_token(self):
        user = await deezer._api_call("deezer.getUserData")
        if user["USER"]["OPTIONS"]["streaming_group"] == "ads":
            raise Exception("Free accounts are not eligible for downloading")


async def set_up_deezer():
    arl = Config.getdata("deezer_arl")
    if len(arl) == 0:
        return (
            "**ERROR**: No deezer arl were provided.\n"
            "Set your arl via: `{}setdata {} deezer_arl"
            " [your arl]`"
        ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])

    try:
        client_id = Config.getdata("deezer_client_id", "579939560")
        client_secret = Config.getdata(
            "deezer_client_secret", "fa31fc13e7a28e7d70bb61e91aa9e178"
        )
        bf_secret = Config.getdata("deezer_bf_secret", "g4el58wc0zvf9na1")
        return await Deezer.create(client_id, client_secret, bf_secret, arl)
    except Exception as e:
        return f"**ERROR**: {e}"


async def deezer_search_keyboard(query: str, page: int = 0):
    keyboard = []
    tracks = await deezer.search_track(query, offset=page * 10, limit=11)

    if not tracks:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("No track was found.", "None")]]
        )

    for track in tracks[:10]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    parse_data("{time} | {name} - {artist}", track),
                    parse_data("deezer trackinfo {id}", track),
                )
            ]
        )

    page_keyboard = []
    if page != 0:
        page_keyboard.append(
            InlineKeyboardButton("Previous Page", f"dese {query} {page-1}")
        )
    if len(tracks) == 11:
        page_keyboard.append(
            InlineKeyboardButton("Next Page", f"dese {query} {page+1}")
        )

    return InlineKeyboardMarkup(keyboard + [page_keyboard])


async def on_data_change():
    global deezer
    deezer = await set_up_deezer()


deezer = None


@Bot.on_message(
    Config.IS_ADMIN
    & filters.regex(
        rf"^{Config.REGEX_CMD_PREFIXES}deezer"
        r"(?: https:\/\/www\.deezer\.com/(?:[a-z]{2}\/)?(?P<type>album|track)"
        r"\/(?P<id>\d+)| (?P<query>.+))?$"
    )
)
@error_handler_decorator
async def deezer_message(_: Bot, message: Message):
    global deezer
    if deezer is None:
        deezer = await set_up_deezer()

    if isinstance(deezer, str):
        await message.reply(deezer)
        return

    match = message.matches[0]
    type = match.group("type")
    id = match.group("id")
    query = match.group("query")

    if query:
        await message.reply(
            f"Results for **{query}**:",
            reply_markup=await deezer_search_keyboard(query),
        )
        return
    elif not id:
        await message.reply(
            f"{Config.CMD_PREFIXES[0]}deezer [album/track url] |"
            " [query to search]"
        )
        return

    try:
        if type == "track":
            data = await deezer.get_track(id)
            cover = await deezer.get_track_cover(track=data)
        else:
            data = await deezer.get_album(id)
            cover = data["cover"]

        keyboard = []
        _keyboard = [
            InlineKeyboardButton(f"Download {type}", f"deezer dl{type} {id}")
        ]
        if type == "track":
            _keyboard.append(
                InlineKeyboardButton("Preview", f"deezer pvtrack {id}")
            )

        keyboard.append(_keyboard)

        if type == "album":
            keyboard += [
                [
                    InlineKeyboardButton("—", "none"),
                    InlineKeyboardButton("Tracks", "none"),
                    InlineKeyboardButton("—", "none"),
                ],
            ]
            keyboard += [
                [
                    InlineKeyboardButton(
                        parse_data("{time} | {name} - {artist}", track),
                        parse_data("deezer dltrack {id}", track),
                    ),
                    InlineKeyboardButton(
                        parse_data("Preview", track),
                        parse_data("deezer pvtrack {id}", track),
                    ),
                ]
                for track in data["songs"]
            ]

        await message.reply_photo(
            cover,
            caption=parse_data("{name} - {artist}", data),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        await message.reply("**ERROR**: " + str(e))


@Bot.on_callback_query(
    Config.IS_ADMIN & filters.regex(r"^deezer (?P<type>\w+) (?P<id>\w+)$")
)
@error_handler_decorator
async def deezer_callback(_: Bot, query: CallbackQuery):
    global deezer
    if deezer is None:
        deezer = await set_up_deezer()

    if isinstance(deezer, str):
        await query.answer(deezer)
        return

    loop = asyncio.get_running_loop()
    info = query.matches[0].groupdict()

    if info["type"] in ["dltrack", "dlalbum"]:
        try:
            await deezer.check_token()
        except Exception as e:
            await query.answer("ERROR: " + str(e))
            return

        await query.answer("Download is in process.")
        download_path = (
            Config.getdata("download_path", "downloads", use_env=True) + "/"
        )

        if info["type"] == "dlalbum":
            album = await deezer.get_album(info["id"])
            tracks = album["songs"]
        else:
            _track = await deezer.get_track(info["id"])
            album = await deezer.get_album(_track["album_id"])
            tracks = [_track]

        _album_path = Config.getdata("deezer_album_path", "{artist}/{name}")
        album_path = download_path + parse_data(_album_path, album) + "/"
        zfill = max(2, len(str(album["tracks_count"])))
        os.makedirs(album_path, exist_ok=True)

        cover_path = album_path + "cover.jpg"
        if not os.path.exists(cover_path):
            cover_url: str = album["cover"]
            cover_msg = await query.message.reply("Downloading **cover.jpg**.")

            if await error_handler(
                download_file,
                kwargs=dict(
                    url=cover_url,
                    filename=cover_path,
                    proxy=Config.PROXY,
                    progress=download_progress,
                    progress_args=("cover.jpg", time(), cover_msg),
                ),
                update=cover_msg,
                text="Failed to download the cover.",
            ):
                if os.path.exists(cover_path):
                    os.remove(cover_path)

                return

            loop.call_later(
                5,
                lambda msg: asyncio.create_task(msg.delete()),
                cover_msg,
            )

        for track in tracks:
            url = await deezer.get_file_url(track)
            track["track_number"] = str(track["track_number"]).zfill(zfill)
            track_msg = await query.message.reply(
                parse_data("Downloading **{name}**.", track)
            )
            _track_name = Config.getdata(
                "deezer_track_name", "{track_number} {name}"
            )
            track["format"] = track["format"].split("_")[0]
            track_name = parse_data(_track_name + ".{format}", track)
            full_path = album_path + track_name
            if os.path.exists(full_path):
                await track_msg.edit(
                    parse_data("Track **{name}** already exists.", track)
                )
                loop.call_later(
                    5,
                    lambda msg: asyncio.create_task(msg.delete()),
                    track_msg,
                )
                continue

            if await error_handler(
                download_file,
                kwargs=dict(
                    url=url,
                    filename=full_path,
                    proxy=Config.PROXY,
                    chunk_size=2048,
                    chunk_process=deezer.decrypt_chunk,
                    chunk_process_args=(track["id"],),
                    progress=download_progress,
                    progress_args=(track_name, time(), track_msg),
                ),
                update=track_msg,
                text=parse_data(
                    "Failed to download the track **{name}**.", track
                ),
            ):
                if os.path.exists(full_path):
                    os.remove(full_path)

                continue

            track["source"] = "Deezer"
            track["album"] = album
            track["date"] = album["release_date"]
            track["lyrics"] = await deezer.get_track_lyrics(track["id"])
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
        track = await deezer.get_track(info["id"])
        cover = await deezer.get_track_cover(track=track)
        await query.message.reply_photo(
            cover,
            caption=parse_data("{name} - {artist}", track),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Download",
                            parse_data("deezer dltrack {id}", track),
                        ),
                        InlineKeyboardButton(
                            parse_data("Preview", track),
                            parse_data("deezer pvtrack {id}", track),
                        ),
                    ]
                ]
            ),
        )
    elif info["type"] == "pvtrack":
        track = await deezer.get_track(info["id"])
        if not track["preview"]:
            await query.message.reply("There is no preview available.")
            return

        await query.message.reply_audio(
            track["preview"],
            caption=parse_data(
                "Preview for **{name}** by **{artist}**.", track
            ),
        )


@Bot.on_callback_query(
    Config.IS_ADMIN & filters.regex(r"^dese (?P<query>.+?) (?P<page>\d+)$")
)
@error_handler_decorator
async def deezer_search(_: Bot, query: CallbackQuery):
    global deezer
    if deezer is None:
        deezer = await set_up_deezer()

    if isinstance(deezer, str):
        await query.answer(deezer)
        return

    search_query, page = query.matches[0].groups()
    await query.edit_message_reply_markup(
        await deezer_search_keyboard(search_query, int(page))
    )


__all__ = ["deezer_message", "deezer_callback", "deezer_search"]
__plugin__ = True
__bot_only__ = True
