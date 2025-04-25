from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config


notes: dict = Config.getdata("notes") or {}


@Client.on_message(
    Config.IS_ADMIN
    & filters.command(
        ["addnote", "getnote", "delnote", "notes"],
        Config.CMD_PREFIXES
    )
)
async def note_message(_: Client, message: Message):
    action = message.command[0]
    match action:
        case "addnote":
            if len(message.command) >= 2:
                note_name = message.command[1]
                if len(message.command) > 2:
                    note = message.text[len(action) + len(note_name) + 3:]
                    notes[note_name] = note
                    Config.setdata("notes", notes)
                    await message.reply(f"Saved note `{note_name}`.")
                    return
                elif message.reply_to_message:
                    await message.reply("Not supported for now.")
                    return
            await message.reply(
                f"{Config.CMD_PREFIXES[0]}addnote [note name]"
                + " [the note or reply to the note message]"
            )
            return


__all__ = ["note_message"]
__plugin__ = True
