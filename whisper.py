import re
import base64
import hashlib
from pyrogram import Client, filters
from cryptography.fernet import Fernet
from pyrogram.types import (
    InlineQuery, CallbackQuery, InlineQueryResultArticle, ChosenInlineResult,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)

from config import Config


whispers: dict = Config.getdata("whispers") or {}


def generate_fernet(user_id: int | str) -> bytes:
    user_id = int(user_id)
    key_bytes = user_id.to_bytes(8, byteorder="big")
    hashed = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)
    return fernet_key


@Client.on_inline_query(
    filters.regex(
        r"^(.+?)\s+@(?P<username>[a-zA-Z_]{3,16})$",
        flags=re.DOTALL
    )
)
async def whisper_inline(_: Client, query: InlineQuery):
    username = query.matches[0].group("username")
    await query.answer(
        [
            InlineQueryResultArticle(
                title=f"A whisper for {username}",
                description="Only they can open it.",
                input_message_content=InputTextMessageContent(
                    f"A whisper for {username}, only they can open it."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Show the message",
                        callback_data="whisper {} {}".format(
                            username, query.from_user.id
                        )
                    )]
                ])
            )
        ],
        cache_time=0
    )


@Client.on_chosen_inline_result()
async def whisper_inline_result(_: Client, chosen: ChosenInlineResult):
    cipher = Fernet(generate_fernet(chosen.from_user.id))
    sentence = chosen.query.rsplit(" ", 1)[0].encode()
    whispers[chosen.inline_message_id] = cipher.encrypt(sentence).decode()
    Config.setdata("whispers", whispers)


@Client.on_callback_query(
    filters.regex(r"^whisper (?P<receiver>.+) (?P<sender>.+)$")
)
async def whisper_callback(_: Client, query: CallbackQuery):
    if query.inline_message_id not in whispers:
        await query.answer("Whisper not found.")
        return

    receiver, sender = query.matches[0].groups()
    text: str = whispers[query.inline_message_id]
    if any(
        id in (receiver, sender)
        for id in (str(query.from_user.id), query.from_user.username)
    ):
        cipher = Fernet(generate_fernet(sender))
        await query.answer(cipher.decrypt(text).decode(), show_alert=True)


__all__ = ["whisper_inline", "whisper_inline_result", "whisper_callback"]
__plugin__ = True
