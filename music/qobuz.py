import os
import time
import httpx
import hashlib
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from .util import download_file, download_progress, parse_data, tag_file

from config import Config


# Qobuz class from https://github.com/OrfiDev/orpheusdl-qobuz
# with some modifications
class Qobuz:
    def __init__(self, app_id: str | int, app_secret: str, auth_token: str):
        self.api_base = "https://www.qobuz.com/api.json/0.2/"
        self._app_id = str(app_id)
        self._app_secret = app_secret
        self._auth_token = auth_token
        self.session = httpx.Client()

    def headers(self):
        return {
            'X-Device-Platform': 'android',
            'X-Device-Model': 'Pixel 3',
            'X-Device-Os-Version': '10',
            'X-User-Auth-Token': self._auth_token,
            "X-Device-Manufacturer-Id": "482D8CB7-015D-402F-A93B-5EEF0E0996F3",
            "X-App-Version": "5.16.1.5",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build" +
            "/QP1A.190711.020) QobuzMobileAndroid/5.16.1.5-b21041415"
        }

    def _get(self, url: str, params=None):
        if not params:
            params = {}

        response = self.session.get(
            self.api_base + url,
            params=params,
            headers=self.headers()
        )

        if response.status_code not in [200, 201, 202]:
            raise Exception(response.json()["message"])

        return response.json()

    def check_token(self):
        params = {
            "app_id": self._app_id,
        }
        params["request_ts"], params["request_sig"] = self.create_signature(
            "user/get", params
        )

        response = self._get("user/get", params)

        if response["credential"]["parameters"]:
            pass
        elif not response["credential"]["parameters"]:
            raise Exception("Free accounts are not eligible for downloading")
        else:
            raise Exception("Invalid UserID/Token")

    def create_signature(self, method: str, parameters: dict):
        timestamp = str(int(time.time()))
        to_hash = method.replace("/", "")

        for key in sorted(parameters.keys()):
            if key not in ["app_id", "user_auth_token"]:
                to_hash += key + parameters[key]

        to_hash += timestamp + self._app_secret
        signature = hashlib.md5(to_hash.encode()).hexdigest()
        return timestamp, signature

    def search(self, query_type: str, query: str, limit: int = 10):
        return self._get(
            "catalog/search",
            params={
                "query": query,
                "type": query_type + "s",
                "limit": limit,
                "app_id": self._app_id
            }
        )

    def get_file_url(self, track_id: str, quality_id=27):
        params = {
            "track_id": track_id,
            "format_id": str(quality_id),
            "intent": "stream",
            "sample": "false",
            "app_id": self._app_id,
            "user_auth_token": self._auth_token
        }

        signature = self.create_signature("track/getFileUrl", params)
        params["request_ts"], params["request_sig"] = signature

        return self._get("track/getFileUrl", params=params)

    def get_track(self, track_id: str):
        return self._get(
            "track/get",
            params={
                "track_id": track_id,
                "app_id": self._app_id
            }
        )

    def get_playlist(self, playlist_id: str):
        return self._get(
            "playlist/get",
            params={
                "playlist_id": playlist_id,
                "app_id": self._app_id,
                "limit": "2000",
                "offset": "0",
                "extra": "tracks,subscribers,focusAll"
            }
        )

    def get_album(self, album_id: str):
        return self._get(
            "album/get",
            params={
                "album_id": album_id,
                "app_id": self._app_id,
                "extra": "albumsFromSameArtist,focusAll"
            }
        )

    def get_artist(self, artist_id: str):
        return self._get(
            "artist/get",
            params={
                "artist_id": artist_id,
                "app_id": self._app_id,
                "extra": "albums,playlists,tracks_appears_on," +
                "albums_with_last_release,focusAll",
                "limit": "1000",
                "offset": "0"
            }
        )


def set_up_qobuz():
    app_id = Config.getdata("qobuz_app_id", "579939560")
    app_secret = Config.getdata(
        "qobuz_app_secret",
        "fa31fc13e7a28e7d70bb61e91aa9e178"
    )
    auth_token = Config.getdata("qobuz_auth_token")
    if not auth_token or len(auth_token) == 0:
        return (
            "**ERROR**: No qobuz token were provided.\n"
            "Set your qobuz token via: `{}setdata {} qobuz_auth_token"
            " [your auth token]`"
        ).format(Config.CMD_PREFIXES[0], __name__.split(".")[-1])
    return Qobuz(app_id, app_secret, auth_token)


def on_data_change():
    global qobuz
    qobuz = set_up_qobuz()


qobuz = set_up_qobuz()

ALBUM_PATH = "{artist}/{name}"
TRACK_NAME = "{track_number} {name}"


@Client.on_message(
    Config.IS_ADMIN
    & filters.regex(
        f"{Config.REGEX_CMD_PREFIXES}qobuz"
        r"(?: https://www\.qobuz\.com/.*/album/.*/(?P<id>\w+))?"
    )
)
async def download_from_qobuz(_: Client, message: Message):
    if isinstance(qobuz, str):
        await message.reply(qobuz)
        return

    album_id = message.matches[0].group("id")

    if not album_id:
        await message.reply(f"{Config.CMD_PREFIXES[0]}qobuz [album url]")
        return

    try:
        album = qobuz.get_album(album_id)
    except Exception as e:
        await message.reply("**ERROR**: " + str(e))
        return

    keyboard = [
        [InlineKeyboardButton(
            "Download the album", f"qobuz dlalbum {album_id}"
        )],
        [
            InlineKeyboardButton("—", "none"),
            InlineKeyboardButton("Tracks", "none"),
            InlineKeyboardButton("—", "none")
        ]
    ]
    tracks = [
        [InlineKeyboardButton(
            parse_data("{name}", track),
            parse_data("qobuz dltrack {id}", track)
        )] for track in album["tracks"]["items"]
    ]
    await message.reply_photo(
        album["image"]["large"],
        caption="Album **{}** by **{}**".format(
            album["title"],
            ", ".join(artist["name"] for artist in album["artists"])
        ),
        reply_markup=InlineKeyboardMarkup(
            keyboard
            + tracks
        )
    )


@Client.on_callback_query(
    Config.IS_ADMIN
    & filters.regex(r"^qobuz (?P<type>\w+) (?P<id>\w+)$")
)
async def qobuz_callback(_: Client, query: CallbackQuery):
    if isinstance(qobuz, str):
        await query.answer(qobuz)
        return

    info = query.matches[0].groupdict()

    if info["type"] in ["dlalbum", "dltrack"]:
        await query.answer("Download is in process")
        download_path = Config.getdata(
            "download_path",
            "downloads",
            use_env=True
        ) + "/"
        if info["type"] == "dlalbum":
            album = qobuz.get_album(info["id"])
            tracks = album["tracks"]["items"]
        elif info["type"] == "dltrack":
            _track = qobuz.get_track(info["id"])
            album = qobuz.get_album(_track["album"]["id"])
            tracks = [_track]
        album_path = download_path + parse_data(ALBUM_PATH, album) + "/"
        zfill = max(2, len(str(album["tracks_count"])))
        os.makedirs(album_path, exist_ok=True)

        cover_path = album_path + "cover.jpg"
        if not os.path.exists(cover_path):
            cover_msg = await query.message.reply("Downloading **cover.jpg**.")
            await download_file(
                album["image"]["large"],
                cover_path,
                progress=download_progress,
                progress_args=("cover.jpg", time.time(), cover_msg)
            )

        for track in tracks:
            stream_data = qobuz.get_file_url(str(track["id"]))
            track.update(stream_data)
            track["track_number"] = str(track["track_number"]).zfill(zfill)
            track_msg = await query.message.reply(
                parse_data("Downloading **{name}**.", track)
            )
            track_name = parse_data(
                TRACK_NAME + ".{format}",
                track
            )
            full_path = album_path + track_name
            if os.path.exists(full_path):
                await track_msg.edit(
                    parse_data("Track **{name}** already exists.", track)
                )
                continue
            await download_file(
                stream_data["url"],
                full_path,
                progress=download_progress,
                progress_args=(track_name, time.time(), track_msg)
            )
            tag_file(full_path, cover_path, track)
        await query.message.reply("Download is done.")


__all__ = ["download_from_qobuz", "qobuz_callback"]
__plugin__ = True
