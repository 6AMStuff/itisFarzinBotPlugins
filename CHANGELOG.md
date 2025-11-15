## v8.4.1 (2025-11-15)

### Fix

- **lastfm**: use tuples for timeframes

## v8.4.0 (2025-11-15)

### Fix

- **lastfm**: handle tracks without an album
- **deezer**: use self in check_token method

## v8.3.0 (2025-09-18)

### Feat

- **qobuz,deezer**: add force_download and force_update
- **deezer**: add album genre field
- **music**: add resume support for downloads
- **misc**: add start plugin
- **qobuz**: add track preview
- **qobuz,deezer**: add a download button to the search results
- **date**: add jalali date command

### Refactor

- **helper**: rename it to misc
- **deezer**: update a comment

## v8.2.0 (2025-07-23)

### Feat

- **group-manager**: log unhandled exceptions
- **group-manager**: add `kickme`
- **group-manager**: add `delban`, `delkick` and `delmute`
- **lastfm**: include album name in the status text

### Refactor

- **weather**: mention weather data source
- **lastfm**: cleanup time frames
- **lastfm**: simplify track and artist names for recent tracks
- change `__all__` from list to tuple

## v8.1.0 (2025-07-13)

### Feat

- **translate**: support inline text translation
- **date**: add date plugin

### Fix

- **music**: resolve unmatched f-string issues for python 3.10
- **deezer**: answer with an empty message for preview

### Refactor

- **trasnlate**: improve response text
- **translate**: improve error message
- `Config` to `Settings`
- **helper**: Improve code and grammar
- **status**: simplify bot detection
- **music**: improve grammar
- **weather**: improve error message

## v8.0.0 (2025-07-08)

### Feat

- **weather**: add weather plugin
- **throw**: add `dice`, `dart`, `basketball`, `bowling`, and `slot` commands
- **throw**: add throw plugin
- **translate**: add translate plugin
- **qrcode**: add qrcode plugin

### Refactor

- **throw**: put all commands in one function

## v7.1.2 (2025-07-08)

### Feat

- **qobuz,deezer**: download tracks as a tmp file at first
- **deezer**: add track preview
- **qobuz,deezer**: improve download is complete text

### Fix

- **qobuz,deezer**: handle edge case during message deletion
- **qobuz,deezer**: ensure correct message deletion
- **qobuz,deezer**: respond to empty command call

## v7.1.1 (2025-07-04)

### Feat

- **qobuz,deezer**: delete download messages after 5 seconds
- **deezer**: add `check_token`
- **music**: add logging.debug for exceptions

### Fix

- **qobuz**: resolve download issues
- **qobuz,deezer**: handle case where no track was found in search
- **music**: prevent double callback answers

### Refactor

- **qobuz**: remove the useless check in `check_token`

## v7.1.0 (2025-06-27)

### Feat

- **lastfm**: add proxy support
- **music**: add retry to downloads
- **music**: fetch track lyrics from deezer
- **music**: add proxy support for downloads
- **music**: improve error handling
- **qobuz**: add proxy support
- **music**: add version to the track title
- **deezer**: add support for track URLs
- **qobuz**: only download the original cover art
- **deezer**: announce when the downloads are done
- **qobuz,deezer**: add try-except to the downloads

### Fix

- **lastfm**: make `set_up_lastfm` and `on_data_change` async
- **lastfm**: initialize lastfm when it is in use
- **music**: use artists instead of artist
- **qobuz,deezer**: answer to the trackinfo callback
- **deezer**: handle empty song contributors
- **deezer**: use `deezer_album_path` for album path

### Refactor

- **music**: answer with an empty message instead of wait
- **status**: use the bot uptime instead of local uptime
- **lastfm**: replace `lastfm_chosen` variable with a lambda function

## v7.0.1 (2025-06-17)

### Feat

- **group-manager**: support cli
- **status**: support cli
- define `__bot_only__`
- **status**: add battery percentage
- **status**: add ping latency

### Refactor

- **status**: clean up inline keyboard

## v7.0.0 (2025-06-10)

### Feat

- **status**: prioritize bot class uptime source
- **status**: add os
- **status**: add python version
- **status**: add system uptime
- **status**: add disk usage
- **status**: add memory usage
- **status**: add uptime

## v6.2.0 (2025-06-08)

### Feat

- **group-manager**: improve the pin/unpin mechanism
- **group-manager**: disable the pin notification
- **group-manager**: announce after pining/unpining a message
- **group-manager**: add `unpin` command
- **group-manager**: add `pin` command

### Fix

- **group-manager**: improve unpinning pinned message

### Refactor

- **group-manager**: clean up code
- **group-manager**: improve insufficient permission error message
- **group-manager**: improve the pin/unpin text

## v6.1.2 (2025-06-08)

### Fix

- **note**: rewrite return early logic
- **whisper**: handle user resolve failure
- **group-manager**: restrict/unrestrict commands should only work in groups

## v6.1.1 (2025-06-03)

### Fix

- **note**: send help text correctly
- **note**: handle flag in `savenote` correctly

### Refactor

- reformat code manually
- Client -> Bot

## v6.1.0 (2025-06-02)

### Feat

- **deezer**: implement pagination for search results
- **deezer**: add `offset` to the `search_track` method
- **qobuz**: implement pagination for search results
- **qobuz**: add `offset` to the `search` method

### Fix

- **deezer,qobuz**: handle client initialization failure
- **note**: `getnote` command reply consistently even with -d flag

## v6.0.2 (2025-05-29)

### Feat

- **note**: allow auto-deletion of /getnote command message

## v6.0.1 (2025-05-28)

### Feat

- **group-manager**: use settings timezone

## v6.0.0 (2025-05-27)

### Feat

- **deezer**: use async for requests
- **deezer**: add support for MP3 tracks
- **deezer**: add support for downloading an album
- **deezer**: use defined proxy for requests
- **deezer**: add download track feature
- **deezer**: implement `get_album` method
- **deezer**: add `trackinfo` callback query
- **deezer**: implement `get_track_cover` method
- **deezer**: implement my own `get_track` method
- **deezer**: add search command
- **deezer**: add my own deezer class
- **deezer**: implement `on_data_change` hook
- **deezer**: add basics
- **deezer**: add proxy support
- **deezer**: add Deezer API

### Fix

- **deezer**: stop execution after handling search query
- **deezer**: improve failure handling during Deezer setup
- **deezer**: fix `get_album` on a track inside an album
- **deezer**: improve track taging

### Refactor

- **deezer**: pycryptodome -> cryptography
- **qobuz**: improve missing data error message
- **lastfm**: improve missing data error message

### Perf

- **deezer**: improve songs fetch for albums
- **deezer**: improve `get_track_cover` method

## v5.3.0 (2025-05-22)

### Feat

- **group-manager**: add support for reason in ban, mute, and kick
- **group-manager**: add year duration support
- **group-manager**: add week duration support
- **group-manager**: add unban/unmute buttons to ban/mute messages

### Fix

- **group-manager**: strip leading whitespace from reason string
- **group-manager**: handle duration overflows
- **group-manager**: avoid showing duration hint for non-duration commands

### Refactor

- **group-manager**: improve user experience
- **group-manager**: move unban and unmute logic to dedicated functions

## v5.2.0 (2025-05-20)

### BREAKING CHANGE

- Adds a new column

### Feat

- **note**: add support for private notes

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
