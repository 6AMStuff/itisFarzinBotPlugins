from typing import Union
from pyrogram import Client, filters, enums
from sqlalchemy import Text, JSON, select, delete
from pyrogram.types import Message, MessageEntity
from sqlalchemy.orm import Session, Mapped, mapped_column

from config import Config, DataBase


class NotesDatabase(DataBase):
    __tablename__ = "notes"

    note_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    type: Mapped[str] = mapped_column(Text())
    text: Mapped[str] = mapped_column(Text(), nullable=True)
    file_id: Mapped[str] = mapped_column(Text(), nullable=True)
    entities: Mapped[list] = mapped_column(JSON(), nullable=True)


_notes: dict = Config.getdata("notes") or {}


def upgrade_to_sql():
    with Session(Config.engine) as session:
        for note_name in _notes:
            note: dict = _notes[note_name]
            session.merge(NotesDatabase(
                note_name=note_name,
                type=note["type"],
                text=note.get("content", note.get("caption")),
                entities=note["entities"]
            ))
        session.commit()
    Config.setdata("notes", {})


def serialize_entities(entities: list[dict]):
    return [
        {
            key: value.name.lower()
            if isinstance(value, enums.MessageEntityType)
            else value.id if key == "user" and value
            else value
            for key, value in entity.__dict__.items()
            if key not in ["_client"]
        }
        for entity in entities
    ]


async def deserialize_entities(
    client: Client,
    entities: Union[list[dict]] = None
):
    if not entities:
        return None

    return [
        MessageEntity(
            type=enums.MessageEntityType[entity["type"].upper()],
            offset=entity["offset"],
            length=entity["length"],
            url=entity.get("url"),
            user=await client.get_users(entity["user"])
            if entity.get("user") else None,
            language=entity.get("language"),
            custom_emoji_id=entity.get("document_id"),
            expandable=entity.get("collapsed"),
            client=client
        )
        for entity in entities
        if hasattr(enums.MessageEntityType, entity["type"].upper())
        if entity["type"] != "bot_command"
    ]


@Client.on_message(
    filters.command(
        ["savenote", "getnote", "delnote", "notes"],
        Config.CMD_PREFIXES
    )
)
async def note_message(app: Client, message: Message):
    action = message.command[0]
    if len(_notes) > 0:
        upgrade_to_sql()

    match action:
        case "savenote" if await Config.IS_ADMIN(app, message):
            if len(message.command) < 2:
                await message.reply(
                    f"{Config.CMD_PREFIXES[0]}{action} [note name]"
                    + " [the note or reply to the note message]"
                )
            note_name = message.command[1]
            if message.reply_to_message:
                msg = message.reply_to_message
                if msg.text:
                    with Session(Config.engine) as session:
                        session.merge(NotesDatabase(
                            note_name=note_name,
                            type="text",
                            text=msg.text,
                            entities=serialize_entities(msg.entities)
                        ))
                        session.commit()
                elif msg.media:
                    with Session(Config.engine) as session:
                        session.merge(NotesDatabase(
                            note_name=note_name,
                            type=msg.media.name.lower(),
                            text=msg.text,
                            entities=serialize_entities(
                                msg.caption.entities
                            ) if msg.caption else None
                        ))
                        session.commit()
                else:
                    await message.reply("Not supported.")
                    return
                await message.reply(f"Saved note `{note_name}`.")
            elif len(message.command) > 2:
                start_index = len(action) + len(note_name) + 3
                note = message.text[start_index:]
                with Session(Config.engine) as session:
                    session.merge(NotesDatabase(
                        note_name=note_name,
                        type="text",
                        text=note,
                        entities=serialize_entities(message.entities)
                    ))
                    session.commit()
                await message.reply(f"Saved note `{note_name}`.")
        case "getnote":
            if len(message.command) != 2:
                await message.reply(
                    f"{Config.CMD_PREFIXES[0]}{action} [note name]"
                )
                return

            note_name = message.command[1]
            with Session(Config.engine) as session:
                data = session.execute(
                    select(NotesDatabase)
                    .where(NotesDatabase.note_name == note_name)
                ).one_or_none()
                if not data:
                    await message.reply(f"Note **{note_name}** doesn't exist.")
                    return

                note: NotesDatabase = data[0]
                if note.type == "text":
                    await message.reply(
                        note.text,
                        entities=await deserialize_entities(
                            app,
                            note.entities
                        )
                    )
                else:
                    await message.reply_cached_media(
                        note.file_id,
                        caption=note.text,
                        caption_entities=await deserialize_entities(
                            app,
                            note.entities
                        )
                    )
        case "delnote" if await Config.IS_ADMIN(app, message):
            if len(message.command) != 2:
                await message.reply(
                    f"{Config.CMD_PREFIXES[0]}{action} [note name]"
                )
                return

            note_name = message.command[1]
            with Session(Config.engine) as session:
                data = session.execute(
                    select(NotesDatabase)
                    .where(NotesDatabase.note_name == note_name)
                ).one_or_none()
                if not data:
                    await message.reply(f"Note **{note_name}** doesn't exist.")
                    return
                session.execute(
                    delete(NotesDatabase)
                    .where(NotesDatabase.note_name == note_name)
                )
                session.commit()
                await message.reply(f"Note **{note_name}** has been deleted.")
        case "notes":
            with Session(Config.engine) as session:
                notes = session.execute(
                    select(NotesDatabase.note_name)
                ).all()
                note_names = [note[0] for note in notes]
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
