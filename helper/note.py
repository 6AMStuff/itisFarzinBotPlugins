from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config


notes: dict = Config.getdata("notes") or {}


@Client.on_message(
    filters.command(
        ["savenote", "getnote", "delnote", "notes"],
        Config.CMD_PREFIXES
    )
)
async def note_message(_: Client, message: Message):
    action = message.command[0]
    match action:
        case "savenote" if await Config.IS_ADMIN(_, message):
            if len(message.command) >= 2:
                note_name = message.command[1]
                if len(message.command) > 2:
                    note = message.text[len(action) + len(note_name) + 3:]
                    notes[note_name] = {"type": "text", "content": note}
                    Config.setdata("notes", notes)
                    await message.reply(f"Saved note `{note_name}`.")
                    return
                elif message.reply_to_message:
                    if message.reply_to_message.text:
                        notes[note_name] = {
                            "type": "text",
                            "content": message.reply_to_message.text
                        }
                        Config.setdata("notes", notes)
                    else:
                        await message.reply("Not supported for now.")
                        return
                    await message.reply(f"Saved note `{note_name}`.")
                    return
            await message.reply(
                f"{Config.CMD_PREFIXES[0]}addnote [note name]"
                + " [the note or reply to the note message]"
            )
        case "getnote":
            if len(message.command) != 2:
                await message.reply(
                    f"{Config.CMD_PREFIXES[0]}getnote [note name]"
                )
                return
            note_name = message.command[1]
            if note_name not in notes:
                await message.reply(f"Note **{note_name}** doesn't exist.")
                return
            note = notes[note_name]
            if isinstance(note, dict):
                if note["type"] == "text":
                    note = note["content"]
            await message.reply(note)
        case "delnote" if await Config.IS_ADMIN(_, message):
            if len(message.command) != 2:
                await message.reply(
                    f"{Config.CMD_PREFIXES[0]}delnote [note name]"
                )
                return
            note_name = message.command[1]
            if note_name not in notes:
                await message.reply(f"Note **{note_name}** doesn't exist.")
                return
            del notes[note_name]
            Config.setdata("notes", notes)
            await message.reply(f"Note {note_name} has been deleted.")
        case "notes":
            note_names = notes.keys()
            if len(note_names) == 0:
                msg = "There are no notes saved."
            else:
                msg = "List of notes:\n"
                for note in note_names:
                    msg += f" - `{note}`\n"
                msg += (
                    "You can retrieve these notes by using `/getnote"
                    + " [notename]`"
                )
            await message.reply(msg)


__all__ = ["note_message"]
__plugin__ = True
