import re
from bot import Bot
from datetime import datetime, timedelta
from pyrogram import filters, errors, utils
from pyrogram.types import (
    Message,
    ChatPermissions,
    Chat,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from settings import Settings


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
    action_text = "unbanned" if result else "failed to unban"

    if by:
        text = f"{by.mention} {action_text} {user.mention}."
    else:
        text = f"{action_text.capitalize()} {user.mention}."

    await (message.edit if by else message.reply)(text)


async def unmute(message: Message, chat: Chat, user: User, by: User = None):
    result = await message._client.restrict_chat_member(
        chat.id,
        user.id,
        chat.permissions,
    )
    action_text = "unmuted" if result else "failed to unmute"

    if by:
        text = f"{by.mention} {action_text} {user.mention}."
    else:
        text = f"{action_text.capitalize()} {user.mention}."

    await (message.edit if by else message.reply)(text)


@Bot.on_message(
    filters.group
    & filters.command(
        [
            "ban",
            "delban",
            "unban",
            "kick",
            "delkick",
            "mute",
            "delmute",
            "unmute",
        ],
        Settings.CMD_PREFIXES,
    )
)
async def restrict(app: Bot, message: Message):
    action = message.command[0]
    operation = "unrestrict" if action in ["unban", "unmute"] else "restrict"
    duration = (message.command[1:] or [None])[0]
    chat = message.chat
    reply_to = message.reply_to_message

    if duration and duration[-1] not in ["y", "w", "d", "h", "m", "s"]:
        duration = None

    start_index = len(action) + (len(duration) + 1 if duration else 0) + 2
    reason = message.text[start_index:].strip()

    if not reply_to:
        arg_hint = " [duration]" if action in ["ban", "mute"] else ""
        arg_hint_2 = " [reason]" if action in ["ban", "mute", "kick"] else ""
        await message.reply(
            f"{Settings.CMD_PREFIXES[0]}{action}{arg_hint} *reply to a user"
            + arg_hint_2
        )
        return

    user = reply_to.from_user
    if not user:
        await message.reply("I can't find this user.")
        return

    chat_member = await app.get_chat_member(chat.id, message.from_user.id)
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            f"You don't have the permission to {operation} this user."
        )
        return

    bot_chat_member = await app.get_chat_member(chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.reply(
            f"I don't have the permission to {operation} this user."
        )
        return

    try:
        replied_chat_member = await app.get_chat_member(chat.id, user.id)
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
            await message.reply(
                "Duration out of range. Please enter a smaller value."
            )
            return

    formatted_date = date.astimezone(Settings.TIMEZONE).strftime(
        "%d/%m/%Y, %H:%M:%S %Z"
    )

    match action:
        case "ban" | "delban":
            try:
                result = await app.ban_chat_member(chat.id, user.id, date)
            except OverflowError:
                await message.reply(
                    "Duration out of range. Please enter a smaller value."
                )
                return

            if action[0:3] == "del":
                try:
                    await reply_to.delete()
                except Exception:
                    pass

            await message.reply(
                "{} {} {}.{}".format(
                    "Banned" if bool(result) else "Failed to ban",
                    user.mention,
                    "until " + formatted_date if duration else "forever",
                    f"\nFor reason: **{reason}**" if reason else "",
                ),
                reply_markup=(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Unban",
                                    f"restrict unban {user.id}",
                                )
                            ]
                        ]
                    )
                    if app.is_bot
                    else None
                ),
            )
        case "unban":
            await unban(message, chat, user)
        case "kick" | "delkick":
            result = await app.ban_chat_member(chat.id, user.id)
            if not bool(result):
                await message.reply("Failed to kick {}.".format(user.mention))
                return

            if action[0:3] == "del":
                try:
                    await reply_to.delete()
                except Exception:
                    pass

            result = await app.unban_chat_member(chat.id, user.id)
            await message.reply(
                "{} {}.{}".format(
                    "Kicked" if result else "Failed to kick",
                    user.mention,
                    f"\nFor reason: **{reason}**" if reason else "",
                ),
            )
        case "mute" | "delmute":
            try:
                result = await app.restrict_chat_member(
                    chat.id,
                    user.id,
                    ChatPermissions(),
                    date,
                )
            except OverflowError:
                await message.reply("Use a lower duration.")
                return

            if action[0:3] == "del":
                try:
                    await reply_to.delete()
                except Exception:
                    pass

            await message.reply(
                "{} {} {}.{}".format(
                    "Muted" if bool(result) else "Failed to mute",
                    user.mention,
                    "until " + formatted_date if duration else "forever",
                    f"\nFor reason: **{reason}**" if reason else "",
                ),
                reply_markup=(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Unmute",
                                    f"restrict unmute {user.id}",
                                )
                            ]
                        ]
                    )
                    if app.is_bot
                    else None
                ),
            )
        case "unmute":
            await unmute(message, chat, user)


@Bot.on_callback_query(
    filters.regex(r"^restrict (?P<action>\w+) (?P<user>\d+)$")
)
async def restrict_callback(app: Bot, query: CallbackQuery):
    action, user_id = query.matches[0].groups()
    message = query.message
    chat = message.chat

    if not message or not chat:
        return

    chat_member = await app.get_chat_member(chat.id, query.from_user.id)
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_restrict_members
    ):
        await query.answer(
            "You don't have the permission to unrestrict this user."
        )
        return

    bot_chat_member = await app.get_chat_member(chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.edit(
            "I don't have the permission to unrestrict this user."
        )
        return

    try:
        restricted_chat_member = await app.get_chat_member(chat.id, user_id)
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.edit(f"An error occurred: {e.MESSAGE}.")
        return

    user = restricted_chat_member.user
    if not user:
        await message.edit("Can't unrestrict this user.")
        return

    match action:
        case "unban":
            await unban(message, chat, user, by=query.from_user)
        case "unmute":
            await unmute(message, chat, user, by=query.from_user)


@Bot.on_message(
    filters.group & filters.command(["kickme"], Settings.CMD_PREFIXES)
)
async def kickme(app: Bot, message: Message):
    user = message.from_user
    chat = message.chat

    bot_chat_member = await app.get_chat_member(chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_restrict_members
    ):
        await message.edit("I don't have the permission to kick you.")
        return

    try:
        replied_chat_member = await app.get_chat_member(chat.id, user.id)
    except errors.exceptions.bad_request_400.UserNotParticipant as e:
        await message.reply(f"An error occurred: {e.MESSAGE}.")
        return

    if replied_chat_member.status.name.lower() in ("owner", "administrator"):
        await message.reply("I can't kick an owner or admin.")
        return

    result = await app.ban_chat_member(chat.id, user.id)
    if not bool(result):
        await message.reply("Failed to kick you.")
        return

    result = await app.unban_chat_member(chat.id, user.id)
    await message.reply(
        ("Kicked {}." if result else "Failed to kick {}.").format(user.mention)
    )


@Bot.on_message(filters.group & filters.command(["pin", "unpin"]))
async def pin(app: Bot, message: Message):
    action = message.command[0]
    chat = message.chat
    reply_to = message.reply_to_message

    if action == "pin" and not reply_to:
        await message.reply("Reply to a message.")
        return

    chat_member = await app.get_chat_member(chat.id, message.from_user.id)
    if (
        not chat_member.privileges
        or not chat_member.privileges.can_pin_messages
    ):
        await message.reply(
            f"You don't have the permission to {action} a message."
        )
        return

    bot_chat_member = await app.get_chat_member(chat.id, app.me.id)
    if (
        not bot_chat_member.privileges
        or not bot_chat_member.privileges.can_pin_messages
    ):
        await message.reply(
            f"I don't have the permission to {action} a message."
        )
        return

    if action == "pin":
        if await reply_to.pin(disable_notification=True):
            await message.reply("I've pinned the replied message.")
        else:
            await message.reply("Failed to pin the replied message.")
    elif action == "unpin":
        if reply_to:
            msg = await app.get_messages(chat.id, reply_to.id)
            if msg.pinned:
                res = await reply_to.unpin()
            else:
                res = False
        else:
            try:
                chat = await app.get_chat(chat.id)
                if chat.pinned_message:
                    res = await app.unpin_chat_message(
                        chat.id, message_id=chat.pinned_message.id
                    )
                else:
                    res = False
            except errors.exceptions.bad_request_400.MessageIdInvalid:
                res = False

        type = "replied" if reply_to else "latest pinned"
        if res:
            await message.reply(f"I've unpinned the {type} message.")
        else:
            await message.reply(f"Failed to unpin the {type} message.")


__all__ = ("restrict", "restrict_callback", "pin")
__plugin__ = True
__bot_only__ = False
