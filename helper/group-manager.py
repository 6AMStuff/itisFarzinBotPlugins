import re
from datetime import datetime, timedelta, timezone
from pyrogram import Client, filters, errors, utils
from pyrogram.types import (
    Message,
    ChatPermissions,
    Chat,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from config import Config


def human_to_timedelta(duration: str):
    regex_pattern = (
        r"(?:(\d+)y)?\s*"
        r"(?:(\d+)w)?\s*"
        r"(?:(\d+)d)?\s*"
        r"(?:(\d+)h)?\s*"
        r"(?:(\d+)m)?\s*"
        r"(?:(\d+)s)?"
    )
    match = re.match(
        regex_pattern,
        duration,
    )

    if not match:
        raise ValueError("Invalid human-readable time format")

    years = int(match.group(1) or 0)
    weeks = int(match.group(2) or 0)
    days = int(match.group(3) or 0)
    hours = int(match.group(4) or 0)
    minutes = int(match.group(5) or 0)
    seconds = int(match.group(6) or 0)

    total_days = (years * 365) + days

    return timedelta(
        weeks=weeks,
        days=total_days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


async def unban(message: Message, chat: Chat, user: User, by: User = None):
    result = await message._client.unban_chat_member(chat.id, user.id)

    if by:
        text = "{} {} {}.".format(
            by.mention,
            "unbanned" if result else "failed to unban",
            user.mention,
        )
    else:
        text = "{} {}.".format(
            "Unbanned" if result else "Failed to unban",
            user.mention,
        )

    await (message.edit if by else message.reply)(text)


async def unmute(message: Message, chat: Chat, user: User, by: User = None):
    result = await message._client.restrict_chat_member(
        chat.id,
        user.id,
        chat.permissions,
    )

    if by:
        text = "{} {} {}.".format(
            by.mention,
            "unmuted" if result else "failed to unmute",
            user.mention,
        )
    else:
        text = "{} {}.".format(
            "Unmuted" if result else "Failed to unmute",
            user.mention,
        )

    await (message.edit if by else message.reply)(text)


@Client.on_message(
    filters.command(
        ["ban", "unban", "kick", "mute", "unmute"], Config.CMD_PREFIXES
    )
)
async def restrict(app: Client, message: Message):
    action = message.command[0]
    operation = "unrestrict" if action in ["unban", "unmute"] else "restrict"
    duration = (message.command[1:] or [None])[0]

    if not message.reply_to_message:
        arg_hint = " [duration]" if action in ["ban", "mute"] else ""
        await message.reply(
            f"{Config.CMD_PREFIXES[0]}{action}{arg_hint} *reply to a user"
        )
        return

    user = message.reply_to_message.from_user
    if not user:
        await message.reply("I can't find this user.")
        return

    chat_member = await app.get_chat_member(
        message.chat.id, message.from_user.id
    )
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            f"You don't have the permission to {operation} this user."
        )
        return

    bot_chat_member = await app.get_chat_member(message.chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            f"I don't have the permission to {operation} this user."
        )
        return

    try:
        replied_chat_member = await app.get_chat_member(
            message.chat.id, user.id
        )
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.reply(f"An error occurred: {e.MESSAGE}.")
        return

    if replied_chat_member.status.name.lower() in ("owner", "administrator"):
        await message.reply(f"You can't {operation} an owner or admin.")
        return

    date = utils.zero_datetime()
    if duration:
        try:
            date = datetime.now() + human_to_timedelta(duration)
        except ValueError:
            await message.reply("Incorrect time format.")
            return
        except OverflowError:
            await message.reply("Use a lower duration.")
            return
    formatted_date = date.astimezone(timezone.utc).strftime(
        "%d/%m/%Y, %H:%M:%S %Z"
    )

    match action:
        case "ban":
            try:
                result = await app.ban_chat_member(
                    message.chat.id, user.id, date
                )
            except OverflowError:
                await message.reply("Use a lower duration.")
                return
            await message.reply(
                "{} {} {}.".format(
                    "Banned" if bool(result) else "Failed to ban",
                    user.mention,
                    "until " + formatted_date if duration else "forever",
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Unban",
                                f"restrict unban {user.id}",
                            )
                        ]
                    ]
                ),
            )
        case "unban":
            await unban(message, message.chat, user)
        case "kick":
            result = await app.ban_chat_member(message.chat.id, user.id)
            if not bool(result):
                await message.reply("Failed to kick {}.".format(user.mention))
                return

            result = await app.unban_chat_member(message.chat.id, user.id)
            await message.reply(
                "{} {}.".format(
                    "Kicked" if result else "Failed to kick",
                    user.mention,
                ),
            )
        case "mute":
            try:
                result = await app.restrict_chat_member(
                    message.chat.id,
                    user.id,
                    ChatPermissions(),
                    date,
                )
            except OverflowError:
                await message.reply("Use a lower duration.")
                return
            await message.reply(
                "{} {} {}.".format(
                    "Muted" if bool(result) else "Failed to mute",
                    user.mention,
                    "until " + formatted_date if duration else "forever",
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Unmute",
                                f"restrict unmute {user.id}",
                            )
                        ]
                    ]
                ),
            )
        case "unmute":
            await unmute(message, message.chat, user)


@Client.on_callback_query(
    filters.regex(r"^restrict (?P<action>\w+) (?P<user>\d+)$")
)
async def restrict_callback(app: Client, query: CallbackQuery):
    action, user_id = query.matches[0].groups()
    message = query.message

    if not message:
        return

    if not message.chat:
        return

    chat_member = await app.get_chat_member(
        message.chat.id, query.from_user.id
    )
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await query.answer(
            "You don't have the permission to unrestrict this user."
        )
        return

    bot_chat_member = await app.get_chat_member(message.chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.edit(
            "I don't have the permission to unrestrict this user."
        )
        return

    try:
        restricted_chat_member = await app.get_chat_member(
            message.chat.id, user_id
        )
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.edit(f"An error occurred: {e.MESSAGE}.")
        return

    user = restricted_chat_member.user
    if not user:
        await message.edit("Can't unrestrict this user.")
        return

    match action:
        case "unban":
            await unban(message, message.chat, user, by=query.from_user)
        case "unmute":
            await unmute(message, message.chat, user, by=query.from_user)


__all__ = ["restrict", "restrict_callback"]
__plugin__ = True
