from pyrogram.types import Message
from pyrogram import Client, filters

from config import Config


@Client.on_message(
    filters.command(["ban"], Config.CMD_PREFIXES)
)
async def restrict(app: Client, message: Message):
    action = message.command[0]
    if not message.reply_to_message:
        await message.reply(
            f"{Config.CMD_PREFIXES[0]}{action} [reply to a user]"
        )
        return

    if not message.reply_to_message.from_user:
        await message.reply("Can't restrict this user.")
        return

    chat_member = await app.get_chat_member(
        message.chat.id,
        message.from_user.id
    )
    bot_chat_member = await app.get_chat_member(
        message.chat.id,
        app.me.id
    )
    replied_chat_member = await app.get_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id
    )
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "You don't have the permission to restrict a user."
        )
        return

    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "I don't have the permission to restrict a user."
        )
        return

    if replied_chat_member.status.name.lower() in ("owner", "administrator"):
        await message.reply("Can't restrict this user.")
        return

    match action:
        case "ban":
            result = await app.ban_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id
            )
            await message.reply(
                "{} {}.".format(
                    "Banned" if bool(result) else "Failed to ban",
                    message.reply_to_message.from_user.mention
                )
            )


__all__ = ["restrict"]
__plugin__ = True
