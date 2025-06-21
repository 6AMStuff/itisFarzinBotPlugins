import copy
import time
import httpx
import datetime
from mutagen.mp3 import MP3
from typing import Callable
from pyrogram.types import Message
from mutagen.id3 import PictureType
from mutagen.flac import FLAC, Picture
from mutagen.id3 import (
    TIT2,
    TPE1,
    TALB,
    TCOM,
    TCON,
    TDRC,
    TCOP,
    COMM,
    TPE2,
    TRCK,
    TPOS,
    APIC,
)


async def download_file(
    url: str,
    filename: str,
    chunk_size: int = None,
    chunk_process: Callable = None,
    chunk_process_args: tuple = None,
    progress: Callable = None,
    progress_args: tuple = None,
):
    progress_args = progress_args or ()
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_update = time.monotonic()

            with open(filename, "wb") as file:
                i = 0
                async for chunk in response.aiter_bytes(chunk_size):
                    if chunk_process:
                        chunk = await chunk_process(
                            i, chunk, *chunk_process_args
                        )

                    file.write(chunk)
                    downloaded += len(chunk)

                    if time.monotonic() - last_update >= 2:
                        if progress:
                            await progress(
                                downloaded, total_size, *progress_args
                            )

                        last_update = time.monotonic()

                    i += 1

            if progress:
                await progress(downloaded, total_size, *progress_args)


async def download_progress(
    current: int,
    total: int,
    file_name: str,
    start_time: float,
    message: Message,
):
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time if elapsed_time > 0 else 0
    percentage = current * 100 / total
    estimated_time = (total - current) / speed if speed > 0 else 0
    megabytes = 1024 * 1024
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
            "=" * int(percentage // 10), " " * (10 - int(percentage // 10))
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
        self.missing_text = (
            missing_text if missing_text is not None else "{{{key}}}"
        )

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
    if "version" in data and data["version"]:
        if "(" not in data["version"]:
            _data["version"] = f"({data['version']})"
        _data["name"] += f" {_data["version"]}"
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
    _data["time"] = datetime.timedelta(seconds=int(data["duration"]))

    return text.format_map(
        DefaultDictMissing(_data, missing_text=missing_text)
    )


def tag_file(file_path: str, image_path: str, track_info: dict):
    track_type = file_path.split(".")[-1].lower()
    if track_type == "flac":
        tagger = FLAC(file_path)

        picture = Picture()
        picture.type = PictureType.COVER_FRONT
        picture.mime = "image/jpeg"

        with open(image_path, "rb") as f:
            picture.data = f.read()

        if len(picture.data) < 4 * 1024 * 1024:
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
        tagger["comment"] = parse_data(
            "Downloaded by itisFarzin's bot. Source: {source}.",
            track_info,
            "Unknown",
        )

        tagger.save(file_path)
    elif track_type == "mp3":
        audio = MP3(file_path)
        audio.add_tags()

        with open(image_path, "rb") as f:
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=f.read(),
                )
            )

        audio.tags["TIT2"] = TIT2(
            encoding=3, text=[parse_data("{name}", track_info)]
        )
        audio.tags["TPE1"] = TPE1(
            encoding=3, text=[parse_data("{artist}", track_info)]
        )
        audio.tags["TALB"] = TALB(
            encoding=3, text=[parse_data("{album_name}", track_info)]
        )
        audio.tags["TPE2"] = TPE2(
            encoding=3, text=[parse_data("{album_artist}", track_info)]
        )
        audio.tags["TRCK"] = TRCK(
            encoding=3,
            text=[
                parse_data("{track_number}", track_info)
                + "/"
                + parse_data("{total_tracks}", track_info)
            ],
        )
        audio.tags["TPOS"] = TPOS(
            encoding=3,
            text=[
                parse_data("{disc_number}", track_info)
                + "/"
                + parse_data("{total_discs}", track_info)
            ],
        )
        audio.tags["TDRC"] = TDRC(
            encoding=3, text=[parse_data("{date}", track_info, "")]
        )
        audio.tags["TCON"] = TCON(
            encoding=3, text=[parse_data("{genre}", track_info, "")]
        )
        audio.tags["TCOM"] = TCOM(
            encoding=3, text=[parse_data("{composer}", track_info)]
        )
        audio.tags["TCOP"] = TCOP(
            encoding=3, text=[parse_data("{copyright}", track_info)]
        )
        audio.tags["COMM"] = COMM(
            encoding=3,
            lang="eng",
            desc="Comment",
            text=[
                parse_data(
                    "Downloaded by itisFarzin's bot. Source: {source}.",
                    track_info,
                    "Unknown",
                )
            ],
        )

        audio.save()


__util__ = True
