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
