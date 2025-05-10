import re
from datetime import datetime, timedelta
from pyrogram import Client, filters, errors, utils
from pyrogram.types import Message, ChatPermissions

from config import Config


def human_to_timedelta(duration: str):
    match = re.match(
        r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?',
        duration
    )

    if not match:
        raise ValueError("Invalid human-readable time format")

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)

    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


@Client.on_message(
    filters.command(
        ["ban", "unban", "kick", "mute", "unmute"],
        Config.CMD_PREFIXES
    )
)
async def restrict(app: Client, message: Message):
    action = message.command[0]
    duration = (message.command[1:] or [None])[0]
    if not message.reply_to_message:
        await message.reply(
            f"{Config.CMD_PREFIXES[0]}{action} [duration] *reply to a user"
        )
        return

    if not message.reply_to_message.from_user:
        await message.reply("Can't (un)restrict this user.")
        return

    chat_member = await app.get_chat_member(
        message.chat.id,
        message.from_user.id
    )
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "You don't have the permission to (un)restrict a user."
        )
        return

    bot_chat_member = await app.get_chat_member(
        message.chat.id,
        app.me.id
    )
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            "I don't have the permission to (un)restrict a user."
        )
        return

    try:
        replied_chat_member = await app.get_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id
        )
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.reply(f"{e.MESSAGE}.")
        return

    if replied_chat_member.status.name.lower() in ("owner", "administrator"):
        await message.reply("Can't (un)restrict this user.")
        return

    date = utils.zero_datetime()
    if duration:
        try:
            date = datetime.now() + human_to_timedelta(duration)
        except Exception:
            await message.reply("Incorrect time format")
            return

    match action:
        case "ban":
            result = await app.ban_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                date
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
                ChatPermissions(),
                date
            )
            await message.reply(
                "{} {}.".format(
                    "Muted" if bool(result) else "Failed to mute",
                    message.reply_to_message.from_user.mention
                )
            )
        case "unmute":
            result = await app.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                message.chat.permissions
            )
            await message.reply(
                "{} {}.".format(
                    "Unmuted" if bool(result) else "Failed to unmute",
                    message.reply_to_message.from_user.mention
                )
            )

__all__ = ["restrict"]
__plugin__ = True
