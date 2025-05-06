from pyrogram import Client, filters, errors
from pyrogram.types import Message, ChatPermissions

from config import Config


@Client.on_message(
    filters.command(["ban", "unban", "kick", "mute"], Config.CMD_PREFIXES)
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
    try:
        replied_chat_member = await app.get_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id
        )
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.reply(f"{e.MESSAGE}.")
        return

    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "You don't have the permission to (un)restrict a user."
        )
        return

    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "I don't have the permission to (un)restrict a user."
        )
        return

    if replied_chat_member.status.name.lower() in ("owner", "administrator"):
        await message.reply("Can't (un)restrict this user.")
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
        case "unban":
            result = await app.unban_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id
            )
            await message.reply(
                "{} {}.".format(
                    "Unbanned" if result else "Failed to unban",
                    message.reply_to_message.from_user.mention
                )
            )
        case "kick":
            result = await app.ban_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id
            )
            if not bool(result):
                await message.reply(
                    "Failed to kick {}.".format(
                        message.reply_to_message.from_user.mention
                    )
                )
                return

            result = await app.unban_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id
            )
            await message.reply(
                "{} {}.".format(
                    "Kicked" if result else "Failed to kick",
                    message.reply_to_message.from_user.mention
                )
            )
        case "mute":
            result = await app.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                ChatPermissions()
            )
            await message.reply(
                "{} {}.".format(
                    "Muted" if bool(result) else "Failed to mute",
                    message.reply_to_message.from_user.mention
                )
            )

__all__ = ["restrict"]
__plugin__ = True
