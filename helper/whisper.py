import re
import base64
import hashlib
from sqlalchemy import Text, select
from cryptography.fernet import Fernet
from pyrogram import Client, filters, errors
from sqlalchemy.orm import Session, Mapped, mapped_column
from pyrogram.types import (
    InlineQuery,
    CallbackQuery,
    InlineQueryResultArticle,
    ChosenInlineResult,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import Config, DataBase


class WhisperDatabase(DataBase):
    __tablename__ = "whispers"

    message_id: Mapped[str] = mapped_column(Text(), primary_key=True)
    text: Mapped[str] = mapped_column(Text())


def generate_fernet(user_id: int | str) -> bytes:
    user_id = int(user_id)
    key_bytes = user_id.to_bytes(8, byteorder="big")
    hashed = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)
    return fernet_key


@Client.on_inline_query(
    filters.regex(r"^(.+?)\s+@(?P<username>[a-zA-Z_]{3,16})$", flags=re.DOTALL)
)
async def whisper_inline(app: Client, query: InlineQuery):
    full_name = username = query.matches[0].group("username")
    try:
        full_name = (await app.get_users(username)).full_name
    except (
        errors.PeerIdInvalid,
        errors.UsernameInvalid,
        errors.UsernameNotOccupied,
    ):
        pass

    await query.answer(
        [
            InlineQueryResultArticle(
                title=f"A whisper for {full_name}",
                description="Only they can open it.",
                input_message_content=InputTextMessageContent(
                    f"A whisper for {full_name}, only they can open it."
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Show the message",
                                callback_data="whisper {} {}".format(
                                    username, query.from_user.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        ],
        cache_time=0,
    )


@Client.on_chosen_inline_result()
async def whisper_inline_result(_: Client, chosen: ChosenInlineResult):
    cipher = Fernet(generate_fernet(chosen.from_user.id))
    sentence = chosen.query.rsplit(" ", 1)[0].encode()
    with Session(Config.engine) as session:
        session.merge(
            WhisperDatabase(
                message_id=chosen.inline_message_id,
                text=cipher.encrypt(sentence).decode(),
            )
        )
        session.commit()


@Client.on_callback_query(
    filters.regex(r"^whisper (?P<receiver>.+) (?P<sender>.+)$")
)
async def whisper_callback(_: Client, query: CallbackQuery):
    with Session(Config.engine) as session:
        text = session.execute(
            select(WhisperDatabase.text).where(
                WhisperDatabase.message_id == query.inline_message_id
            )
        ).scalar()
        if not text:
            await query.answer("Whisper not found.")
            return

        receiver, sender = query.matches[0].groups()
        if any(
            id in (receiver, sender)
            for id in (str(query.from_user.id), query.from_user.username)
        ):
            cipher = Fernet(generate_fernet(sender))
            await query.answer(cipher.decrypt(text).decode(), show_alert=True)


__all__ = ["whisper_inline", "whisper_inline_result", "whisper_callback"]
__plugin__ = True
