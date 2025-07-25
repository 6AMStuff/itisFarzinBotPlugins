from bot import Bot
from typing import Union
from pyrogram import filters, enums, errors
from pyrogram.types import Message, MessageEntity
from sqlalchemy.orm import Session, Mapped, mapped_column
from sqlalchemy import Text, JSON, Boolean, select, delete

from settings import Settings, DataBase


class NotesDatabase(DataBase):
    __tablename__ = "notes"

    note_name: Mapped[str] = mapped_column(Text(), primary_key=True)
    type: Mapped[str] = mapped_column(Text())
    text: Mapped[str] = mapped_column(Text(), nullable=True)
    file_id: Mapped[str] = mapped_column(Text(), nullable=True)
    entities: Mapped[list] = mapped_column(JSON(), nullable=True)
    private: Mapped[bool] = mapped_column(Boolean(), default=False)


_notes: dict = Settings.getdata("notes") or {}


def upgrade_to_sql():
    with Session(Settings.engine) as session:
        for note_name in _notes:
            note: dict = _notes[note_name]
            session.merge(
                NotesDatabase(
                    note_name=note_name,
                    type=note["type"],
                    text=note.get("content", note.get("caption")),
                    entities=note["entities"],
                )
            )
        session.commit()

    Settings.setdata("notes", {})


def serialize_entities(entities: Union[list[MessageEntity]] = None):
    if not entities:
        return None

    return [
        {
            key: (
                value.name.lower()
                if isinstance(value, enums.MessageEntityType)
                else value.id if key == "user" and value else value
            )
            for key, value in entity.__dict__.items()
            if key not in ["_client"] and value is not None
        }
        for entity in entities
    ]


async def deserialize_entities(
    client: Bot, entities: Union[list[dict[str, str]]] = None
):
    if not entities:
        return None

    return [
        MessageEntity(
            type=enums.MessageEntityType[entity["type"].upper()],
            offset=entity["offset"],
            length=entity["length"],
            url=entity.get("url"),
            user=(
                await client.get_users(entity["user"])
                if entity.get("user")
                else None
            ),
            language=entity.get("language"),
            custom_emoji_id=entity.get("document_id"),
            expandable=entity.get("collapsed"),
            client=client,
        )
        for entity in entities
        if (
            entity
            and hasattr(enums.MessageEntityType, entity["type"].upper())
            and entity["type"] != "bot_command"
        )
    ]


@Bot.on_message(
    filters.command(
        ["savenote", "getnote", "delnote", "notes"], Settings.CMD_PREFIXES
    )
)
async def note_message(app: Bot, message: Message):
    action = message.command[0]
    if len(_notes) > 0:
        upgrade_to_sql()

    match action:
        case "savenote" if await Settings.IS_ADMIN(app, message):
            if (
                len(message.command) == 2 and not message.reply_to_message
            ) or len(message.command) == 1:
                await message.reply(
                    f"{Settings.CMD_PREFIXES[0]}{action} [note name]"
                    + " [the note or reply to the note message]"
                )
                return

            note_name = message.command[1]
            flag = message.command[-1]
            if flag and flag[0] != "-":
                flag = ""

            if message.reply_to_message:
                msg = message.reply_to_message
                if msg.text:
                    with Session(Settings.engine) as session:
                        session.merge(
                            NotesDatabase(
                                note_name=note_name,
                                type="text",
                                text=msg.text,
                                entities=serialize_entities(msg.entities),
                                private=flag in ["-p", "--private"],
                            )
                        )
                        session.commit()
                elif msg.media:
                    with Session(Settings.engine) as session:
                        session.merge(
                            NotesDatabase(
                                note_name=note_name,
                                type=msg.media.name.lower(),
                                text=msg.caption,
                                file_id=getattr(
                                    msg, msg.media.name.lower()
                                ).file_id,
                                entities=(
                                    serialize_entities(msg.caption.entities)
                                    if msg.caption
                                    else None
                                ),
                                private=flag in ["-p", "--private"],
                            )
                        )
                        session.commit()
                else:
                    await message.reply("This message type is not supported.")
                    return

                await message.reply(f"Saved note `{note_name}`.")
            elif len(message.command) > 2:
                start_index = len(action) + len(note_name) + 3
                text = message.text[start_index:].removesuffix(flag)

                if len(text) != 0:
                    with Session(Settings.engine) as session:
                        session.merge(
                            NotesDatabase(
                                note_name=note_name,
                                type="text",
                                text=text,
                                entities=serialize_entities(message.entities),
                                private=flag in ["-p", "--private"],
                            )
                        )
                        session.commit()

                    await message.reply(f"Saved note `{note_name}`.")
        case "getnote":
            if len(message.command) < 2:
                await message.reply(
                    f"{Settings.CMD_PREFIXES[0]}{action} [note name]"
                )
                return

            note_name = message.command[1]
            flag = message.command[-1]
            quote = True
            with Session(Settings.engine) as session:
                data = session.execute(
                    select(NotesDatabase).where(
                        NotesDatabase.note_name == note_name
                    )
                ).one_or_none()
                if not data:
                    await message.reply(f"Note **{note_name}** doesn't exist.")
                    return

                note: NotesDatabase = data[0]
                msg = (
                    message.reply_to_message
                    if message.reply_to_message
                    else message
                )

                if note.private and not await Settings.IS_ADMIN(app, message):
                    await message.reply("You don't have access to this note.")
                    return

                if flag in ["-d", "--delete"] and await Settings.IS_ADMIN(
                    app, message
                ):
                    try:
                        await message.delete()
                        quote = bool(message.reply_to_message)
                    except errors.MessageDeleteForbidden:
                        pass

                if note.type == "text":
                    await msg.reply(
                        note.text,
                        quote=quote,
                        entities=await deserialize_entities(
                            app, note.entities
                        ),
                    )
                else:
                    await msg.reply_cached_media(
                        note.file_id,
                        quote=quote,
                        caption=note.text,
                        caption_entities=await deserialize_entities(
                            app, note.entities
                        ),
                    )
        case "delnote" if await Settings.IS_ADMIN(app, message):
            if len(message.command) != 2:
                await message.reply(
                    f"{Settings.CMD_PREFIXES[0]}{action} [note name]"
                )
                return

            note_name = message.command[1]
            with Session(Settings.engine) as session:
                data = session.execute(
                    select(NotesDatabase).where(
                        NotesDatabase.note_name == note_name
                    )
                ).one_or_none()
                if not data:
                    await message.reply(f"Note **{note_name}** doesn't exist.")
                    return

                session.execute(
                    delete(NotesDatabase).where(
                        NotesDatabase.note_name == note_name
                    )
                )
                session.commit()

            await message.reply(f"Note **{note_name}** has been deleted.")
        case "notes":
            with Session(Settings.engine) as session:
                notes = session.execute(
                    select(NotesDatabase.note_name, NotesDatabase.private)
                ).all()
                notes: dict[str, bool] = {note[0]: note[1] for note in notes}
                if len(notes) == 0:
                    msg = "You haven't saved any notes yet."
                else:
                    msg = "List of notes:\n"
                    for note in notes:
                        msg += " - `{}`{}\n".format(
                            note, " *private" if notes[note] else ""
                        )
                    msg += "Retrieve notes using `/getnote [notename]`"
                await message.reply(msg)


__all__ = ("note_message",)
__plugin__ = True
__bot_only__ = False
