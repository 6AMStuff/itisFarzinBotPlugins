import re
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQuery, CallbackQuery, InlineQueryResultArticle, ChosenInlineResult,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)

from config import Config


whispers: dict = Config.getdata("whispers") or {}


@Client.on_inline_query(
    filters.regex(
        r"^(?P<sentence>.+?)\s+@(?P<username>[a-zA-Z_]{3,16})$",
        flags=re.DOTALL
    )
)
async def whisper_inline(_: Client, query: InlineQuery):
    _, username = query.matches[0].groups()
    await query.answer(
        [
            InlineQueryResultArticle(
                title=f"A whisper for {username}",
                description="Only they can open it.",
                input_message_content=InputTextMessageContent(
                    f"A whisper for {username}, Only they can open it."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Show the message",
                        callback_data="whisper {},{}".format(
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
    sentence, username = chosen.query.rsplit(" @", 1)
    whispers[chosen.inline_message_id] = {
        "sentence": sentence,
        "user": username
    }
    Config.setdata("whispers", whispers)


@Client.on_callback_query()
async def whisper_callback(_: Client, query: CallbackQuery):
    pass


__all__ = ["whisper_inline", "whisper_inline_result", "whisper_callback"]
__plugin__ = True
