from pyrogram import Client
from pyrogram.types import InlineQuery, ChosenInlineResult


@Client.on_inline_query()
async def lastfm_inline(_: Client, query: InlineQuery):
    pass


@Client.on_chosen_inline_result()
async def lastfm_inline_result(_: Client, chosen: ChosenInlineResult):
    pass


__all__ = ["lastfm_inline", "lastfm_inline_result"]
__plugin__ = True
