from pyrogram import Client
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChosenInlineResult
)


@Client.on_inline_query()
async def lastfm_inline(_: Client, query: InlineQuery):
    await query.answer(
        [
            InlineQueryResultArticle(
                title="Status",
                input_message_content=InputTextMessageContent("Status"),
                id="status"
            )
        ],
        cache_time=0
    )


@Client.on_chosen_inline_result()
async def lastfm_inline_result(_: Client, chosen: ChosenInlineResult):
    pass


__all__ = ["lastfm_inline", "lastfm_inline_result"]
__plugin__ = True
