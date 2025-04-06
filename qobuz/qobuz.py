import os
import copy
import time
import httpx
import hashlib
from typing import Callable
from mutagen.id3 import PictureType
from pyrogram import Client, filters
from mutagen.flac import FLAC, Picture
from pyrogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton)

from config import Config


# Qobuz class from https://github.com/OrfiDev/orpheusdl-qobuz
# with some modifications
class Qobuz:
    def __init__(self, app_id: str | int, app_secret: str, auth_token: str):
        self.api_base = 'https://www.qobuz.com/api.json/0.2/'
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

        r = self.session.get(
            self.api_base + url,
            params=params,
            headers=self.headers()
        )

        if r.status_code not in [200, 201, 202]:
            raise Exception(r.json()["message"])

        return r.json()

    def check_token(self):
        params = {
            "app_id": self._app_id,
        }
        signature = self.create_signature("user/get", params)
        params["request_ts"] = signature[0]
        params["request_sig"] = signature[1]

        r = self._get("user/get", params)

        if r["credential"]["parameters"]:
            pass
        elif not r["credential"]["parameters"]:
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


async def download_file(
    url: str,
    filename: str,
    progress: Callable = None,
    progress_args: tuple = None
):
    progress_args = progress_args or ()
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_update = time.monotonic()

            with open(filename, "wb") as file:
                async for chunk in response.aiter_bytes():
                    file.write(chunk)
                    downloaded += len(chunk)

                    if time.monotonic() - last_update >= 2:
                        if progress:
                            await progress(
                                downloaded,
                                total_size,
                                *progress_args
                            )
                        last_update = time.monotonic()
            if progress:
                await progress(downloaded, total_size, *progress_args)


async def download_progress(
    current: int,
    total: int,
    file_name: str,
    start_time: float,
    message: Message
):
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time if elapsed_time > 0 else 0
    percentage = current * 100 / total
    estimated_time = (total - current) / speed if speed > 0 else 0
    megabytes = (1024 * 1024)
    file_size = total / megabytes

    if percentage == 100:
        progress_text = (
            f"**Downloaded**: **{file_name}**\n"
            f"**File Size**: {file_size:.2f} MB\n"
            f"**Estimated Speed**: {file_size / elapsed_time:.2f} MB/s\n"
            f"**Download completed in {elapsed_time:.2f} seconds.**"
        )
    else:
        progress_bar = "[{} {}]".format(
            "=" * int(percentage // 10),
            " " * (10 - int(percentage // 10))
        )
        progress_text = (
            f"**Downloading**: **{file_name}**\n"
            f"{progress_bar} {percentage:.2f}%\n"
            f"**Downloaded**: {current / megabytes:.2f} MB"
            f" of {total / megabytes:.2f} MB\n"
            f"**Speed**: {speed / megabytes:.2f} MB/s\n"
            "**ETA**: "
            f"{time.strftime("%H:%M:%S", time.gmtime(estimated_time))}"
        )

    try:
        await message.edit(progress_text)
    except Exception:
        pass


class DefaultDictMissing(dict):
    def __init__(self, *args, missing_text: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.missing_text = missing_text or "{{{key}}}"

    def __missing__(self, key):
        return self.missing_text.format(key=key)


def parse_data(text: str, data: dict, missing_text: str = None):
    _data = copy.deepcopy(data)
    if "performer" in data:
        _data["artist"] = data["performer"]["name"]
    elif "artist" in data:
        _data["artist"] = data["artist"]["name"]
    if "title" in data:
        _data["name"] = data["title"]
    if "format_id" in data:
        _data["format"] = "flac" if _data["format_id"] in {6, 7, 27} else "mp3"
    if "album" in data:
        _data["album_title"] = data["album"]["title"]
        _data["album_name"] = data["album"]["title"]
        _data["album_artist"] = data["album"]["artist"]["name"]
        _data["total_tracks"] = data["album"]["tracks_count"]
        _data["total_discs"] = data["album"]["media_count"]
    if "release_date_original" in data:
        _data["date"] = data["release_date_original"]
    if "genre" in data.get("album", {}):
        _data["genre"] = data["album"]["genre"]["name"]
    if "composer" in data:
        _data["composer"] = data["composer"]["name"]
    if "media_number" in data:
        _data["disc_number"] = data["media_number"]

    return text.format_map(
        DefaultDictMissing(_data, missing_text=missing_text)
    )


def tag_file(file_path: str, image_path: str, track_info: dict):
    track_type = file_path.split(".")[-1].lower()

    if track_type == "flac":
        tagger = FLAC(file_path)

        picture = Picture()
        with open(image_path, "rb") as f:
            picture.data = f.read()
        picture.type = PictureType.COVER_FRONT
        picture.mime = u"image/jpeg"
        if len(picture.data) > 4 * 1024:
            tagger.add_picture(picture)

        tagger["title"] = parse_data("{name}", track_info)
        tagger["artist"] = parse_data("{artist}", track_info)
        tagger["album"] = parse_data("{album_name}", track_info)
        tagger["albumartist"] = parse_data("{album_artist}", track_info)
        tagger["tracknumber"] = parse_data("{track_number}", track_info)
        tagger["totaltracks"] = parse_data("{total_tracks}", track_info)
        tagger["discnumber"] = parse_data("{disc_number}", track_info)
        tagger["totaldiscs"] = parse_data("{total_discs}", track_info)
        tagger["date"] = parse_data("{date}", track_info, "")
        tagger["genre"] = parse_data("{genre}", track_info, "")
        tagger["composer"] = parse_data("{composer}", track_info)
        tagger["copyright"] = parse_data("{copyright}", track_info)
        tagger["comment"] = "Downloaded by itisFarzin's bot"

        tagger.save(file_path)


def set_up_qobuz():
    app_id = Config.getdata("qobuz_app_id", "579939560")
    app_secret = Config.getdata(
        "qobuz_app_secret",
        "fa31fc13e7a28e7d70bb61e91aa9e178"
    )
    auth_token = Config.getdata("qobuz_auth_token")
    if not auth_token or len(auth_token) == 0:
        return (
            "**ERROR**: No qobuz token were provided."
            f"Set your qobuz token via: `/setdata {__name__.split('.')[-1]}"
            " qobuz_auth_token [your auth token]`"
        )
    return Qobuz(app_id, app_secret, auth_token)


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
        [InlineKeyboardButton("Tracks", "none")]
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
        _.stop_transmission()
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
