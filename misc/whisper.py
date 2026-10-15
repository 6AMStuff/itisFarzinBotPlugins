import base64
import hashlib
import re

from cryptography.fernet import Fernet
from itisfarzinbot import Bot
from itisfarzinbot.settings import DataBase, Settings
from pyrogram import enums, errors, filters
from pyrogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from sqlalchemy import Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column


class WhisperDatabase(DataBase):
    __tablename__ = "whispers"
    __table_args__ = {"extend_existing": True}

    message_id: Mapped[str] = mapped_column(Text(), primary_key=True)
    text: Mapped[str] = mapped_column(Text())


def generate_fernet(user_id: int | str) -> bytes:
    user_id = int(user_id)
    key_bytes = user_id.to_bytes(8, byteorder="big")
    hashed = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)
    return fernet_key


async def whisper_chosen_filter(_, __, chosen: ChosenInlineResult):
    return chosen.result_id == "whisper"


whisper_chosen = filters.create(whisper_chosen_filter)


@Bot.on_inline_query(
    filters.regex(
        r"^(.+?)\s+@(?P<username>[a-zA-Z0-9_]{3,16})$", flags=re.DOTALL
    )
)
async def whisper_inline(app: Bot, query: InlineQuery):
    if not isinstance(query.matches, list) or len(query.matches) == 0:
        return

    full_name = username = query.matches[0].group("username")
    try:
        user = await app.get_users([username])
        if user:
            full_name = user[0].full_name
    except (
        errors.PeerIdInvalid,
        errors.UsernameInvalid,
        errors.UsernameNotOccupied,
    ):
        pass

    await query.answer(
        [
            InlineQueryResultArticle(
                title=f"A whisper for {full_name}.",
                description="Only they can open it.",
                input_message_content=InputTextMessageContent(
                    f"A whisper for {full_name}. Only they can open it.",
                    parse_mode=enums.ParseMode.DISABLED,
                ),
                id="whisper",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Show the whisper",
                                callback_data=f"whisper {username} {query.from_user.id}",
                            )
                        ]
                    ]
                ),
            )
        ],
        cache_time=0,
    )


@Bot.on_chosen_inline_result(whisper_chosen)
async def whisper_inline_result(_: Bot, chosen: ChosenInlineResult):
    cipher = Fernet(generate_fernet(chosen.from_user.id))
    sentence = chosen.query.rsplit(" ", 1)[0].encode()
    with Session(Settings.engine) as session:
        session.merge(
            WhisperDatabase(
                message_id=chosen.inline_message_id,
                text=cipher.encrypt(sentence).decode(),
            )
        )
        session.commit()


@Bot.on_callback_query(
    filters.regex(r"^whisper (?P<receiver>.+) (?P<sender>.+)$")
)
async def whisper_callback(_: Bot, query: CallbackQuery):
    with Session(Settings.engine) as session:
        text = session.execute(
            select(WhisperDatabase.text).where(
                WhisperDatabase.message_id == query.inline_message_id
            )
        ).scalar()
        if not text:
            await query.answer("Whisper not found.")
            return

        if not isinstance(query.matches, list) or len(query.matches) == 0:
            return

        receiver, sender = query.matches[0].groups()
        if any(
            id in (receiver, sender)
            for id in (str(query.from_user.id), query.from_user.username)
        ):
            cipher = Fernet(generate_fernet(sender))
            await query.answer(cipher.decrypt(text).decode(), show_alert=True)


__all__ = ("whisper_callback", "whisper_inline", "whisper_inline_result")
__plugin__ = True
__bot_only__ = True
