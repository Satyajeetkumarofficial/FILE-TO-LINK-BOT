import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from info import * 

BYPASS_IDS = ADMINS + AUTH_CHANNEL + [BIN_CHANNEL, LOG_CHANNEL, PREMIUM_LOGS, VERIFIED_LOG]

@Client.on_message(~filters.service, group=0)  # group=0 allows continue_propagation
async def maintenance_checker(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    if MAINTENANCE_MODE and user_id not in BYPASS_IDS and chat_id not in BYPASS_IDS:
        await message.reply(
    "🚧 <b>Bot is under Maintenance!</b>\n\n"
    "Please try again later.\n\n"
    'Support Group: <a href="https://t.me/ProBotsDiscussionsGroup">➜ Open Chat</a>',
    quote=True,
    parse_mode=ParseMode.HTML
)
        return

    await message.continue_propagation()
