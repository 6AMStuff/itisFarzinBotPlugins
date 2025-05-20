## v5.1.1 (2025-05-20)

### Perf

- **LastFM**: only use `get_recent_tracks`

## v5.1.0 (2025-05-18)

### Feat

- **note**: reply with note if command is reply

## v5.0.7 (2025-05-14)

### Fix

- **whisper**: disable parse mode in whisper notification message

### Refactor

- **note**: update the parameter types of `serialize_entities` and `deserialize_entities`

### Perf

- **whisper**: improve chosen inline handler filter

## v5.0.6 (2025-05-12)

### Feat

- **config**: add pyproject.toml support for flake8

### Fix

- **note**: return None when entities is None in `serialize_entities`

## v5.0.5 (2025-05-12)

### Fix

- **whisper**: add filter to handle only chosen inlines for whisper
- **LastFM**: add filter to handle only chosen inlines for LastFM

## v5.0.4 (2025-05-12)

### Fix

- **note**: don't parse empty entity
- **note**: save media caption
- **note**: save media file_id

### Perf

- **note**: don't save entity parameters with None value

## v5.0.3 (2025-05-12)

### Fix

- **LastFM**: move inline query handler to group 1

## v5.0.2 (2025-05-12)

### Fix

- **whisper**: update username regex to allow numbers
- **whisper**: expand exception handling for usernames

### Refactor

- **whisper**: move it to the helper folder
- **LastFM**: use LastFM direct track URL instead of search URL

## v5.0.1 (2025-05-10)

### Fix

- **LastFM**: handle if `get_now_playing` is None

## v5.0.0 (2025-05-10)

### Feat

- **group-manager**: add ban and mute durations to the message
- **group-manager**: add support for duration in ban and mute command
- **group-manager**: add unmute command
- **group-manager**: add mute command
- **group-manager**: add kick command
- **group-manager**: add unban command
- **group-manager**: add ban command

### Fix

- **group-manager**: handle case when user is not a member of the chat

### Perf

- **group-manager**: move around privilege if-statements

## v4.0.1 (2025-05-10)

### Feat

- **config**: configure pre commit
- **config**: configure black and flake8

### Refactor

- **note**: simplify note extraction logic

## v4.0.0 (2025-05-09)

### Feat

- **LastFM**: show a notification to the user to wait
- **LastFM**: add user's top artists/albums/tracks
- **LastFM**: add LastFM expanded status result query
- **LastFM**: use the recent / playing now track cover
- **LastFM**: add user play count to tracks
- **LastFM**: fully utilize `get_recent_tracks`
- **LastFM**: append relative time
- **LastFM**: add expanded mode
- **LastFM**: handle LastFM errors in `lastfm_status`
- **LastFM**: add refresh button
- **LastFM**: add show cover button
- **LastFM**: save login password in md5
- **LastFM**: hyperlink track title to search page
- **LastFM**: add LastFM prefix to texts and id
- **LastFM**: add LastFM status
- **LastFM**: add status to inline query
- **LastFM**: add basics

### Fix

- **LastFM**: add `lastfm_callback` to `__all__`

### Refactor

- **LastFM**: improve text for user's top artists, albums, and tracks
- **LastFM**: [TMP] use `get_now_playing` alongside `get_recent_tracks`

### Perf

- **LastFM**: optimize play timestamp handling

## v3.4.0 (2025-05-09)

### Feat

- **whisper**: display receiver's full name in whisper message

## v3.3.1 (2025-05-06)

### Refactor

- **note**: replace hardcoded cmd with `action` var

## v3.3.0 (2025-05-05)

### BREAKING CHANGE

- get_playlist and get_artist are not used anywhere. If I want to use them, I'll bring them back.

### Feat

- **music**: state source of tracks in track's comment

### Refactor

- **Qobuz**: remove unused methods

## v3.2.1 (2025-05-05)

## v3.2.0 (2025-05-04)

### Feat

- **Qobuz**: use async for requests
- **Qobuz**: use `org` size cover for tracks

## v3.1.1 (2025-05-04)

### Feat

- **note**: prioritize saving replied message

### Fix

- **note**: don't parse `bot_command` entity

### Refactor

- **note**: return early when saving note if args < 2

## v3.1.0 (2025-05-04)

### Feat

- **requirements**: add `sqlalchemy`
- **whisper**: switch to SQL

## v3.0 (2025-04-29)

### Feat

- **whisper**: switch to SQL
- **whisper**: change callback data separator
- **whisper**: encrypt whispers
- **whisper**: display the whisper
- **whisper**: save the whisper
- **whisper**: add the inline query regex
- **whisper**: add basics

### Fix

- **whisper**: correct user validation logic

## v2.0 (2025-04-29)

### Feat

- **note**: support `TEXT_MENTION` in entities
- **note**: support media
- **note**: support `entities`
- **note**: allow non-admin users use `getnote` and `notes`
- **note**: support saving from replied text
- **note**: add type to notes
- **note**: add `notes`
- **note**: add `delnote`
- **note**: add `getnote`
- **note**: change `addnote` to `savenote`
- **note**: add `addnote`
- **note**: define commands
- **note**: add basics

### Fix

- **note**: skip parsing `user` in `entities` when `None`
- **note**: `return` when argument count is incorrect

## v1.0 (2025-04-29)

### Feat

- **Qobuz**: make album path and track name configurable
- **music**: mention track's duration in keyboards
- **Qobuz**: add search track command
- **Qobuz**: check the auth token before downloading
- **qobuz**: implement `on_data_change` hook
- **music**: split qobuz plugin into two main and util plugin
- add dummy buttons before and after the tracks button
- rename qobuz folder to music
- add `__all__` to Qobuz
- add installation section to the README
- add `requirements.txt`
- remove a leftover test
- switch to `httpx` from `requests` in Qobuz plugin
- don't embed the album cover when it's over 4MB
- add `copyright` tag
- add `totaltracks` and `totaldiscs` tag
- append several tags to the tracks
- embed the album cover into FLAC tracks
- download the album cover
- include the `download_path` inside `album_path`
- add Qobuz downloader
- ignore pycache folder
- Add a description for this repo
- initialize readme
- Add license

### Fix

- don't embed the album cover when it's over 4MB
- save the track tag
- convert exception to str
