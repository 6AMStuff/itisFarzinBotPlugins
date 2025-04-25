from pyrogram import Client, filters, enums
from pyrogram.types import Message, MessageEntity

from config import Config


notes: dict = Config.getdata("notes") or {}


def serialize_entities(entities: list[dict]):
    return [
        {
            key: value.name.lower()
            if isinstance(value, enums.MessageEntityType)
            else value
            for key, value in entity.__dict__.items()
            if key not in ["_client", "user"]
        }
        for entity in entities
    ]


def deserialize_entities(entities: list[dict]):
    return [
        MessageEntity(
            type=enums.MessageEntityType[entity["type"].upper()],
            offset=entity["offset"],
            length=entity["length"],
            url=entity.get("url"),
            user=None,
            language=entity.get("language"),
            custom_emoji_id=entity.get("document_id"),
            expandable=entity.get("collapsed"),
            client=None
        )
        for entity in entities
        if hasattr(enums.MessageEntityType, entity["type"].upper())
        if entity["type"].upper() != "TEXT_MENTION"
    ]


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
                    notes[note_name] = {
                        "type": "text",
                        "content": note,
                        "entities": serialize_entities(message.entities)
                    }
                    Config.setdata("notes", notes)
                    await message.reply(f"Saved note `{note_name}`.")
                    return
                elif message.reply_to_message:
                    msg = message.reply_to_message
                    if msg.text:
                        notes[note_name] = {
                            "type": "text",
                            "content": msg.text,
                            "entities": serialize_entities(msg.entities)
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
            entities = None
            if isinstance(note, dict):
                if note["type"] == "text":
                    entities = deserialize_entities(note["entities"])
                    note = note["content"]
            await message.reply(note, entities=entities)
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
            await message.reply(f"Note **{note_name}** has been deleted.")
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
