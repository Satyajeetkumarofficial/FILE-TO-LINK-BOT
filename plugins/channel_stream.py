import asyncio
import os
import random
from web.utils.file_properties import get_hash
from pyrogram import Client, filters, enums
from info import (
    BIN_CHANNEL, URL, CHANNEL, BOT_USERNAME,
    IS_SHORTLINK, CHANNEL_FILE_CAPTION,
    HOW_TO_OPEN, NO_STREAM_CHANNELS
)
from utils import get_size, get_shortlink
from Script import script
from database.users_db import db
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_message(
    filters.channel & (filters.document | filters.video) & ~filters.forwarded,
    group=-1
)
async def channel_receive_handler(bot: Client, broadcast: Message):
    try:
        chat_id = broadcast.chat.id

        # ───── Channel ban check ─────
        if str(chat_id).startswith("-100"):
            is_banned = await db.is_channel_blocked(chat_id)
            if is_banned:
                try:
                    await bot.send_message(
                        chat_id,
                        "🚫 **This channel is banned from using the bot.**\n\n"
                        "🔄 **Contact admin if you think this is a mistake.**\n\n"
                        "@ProBotUpdate"
                    )
                except:
                    pass
                await bot.leave_chat(chat_id)
                return

        # ───── File handling ─────
        file = broadcast.document or broadcast.video
        file_name = file.file_name if file else "Unknown File"

        msg = await broadcast.forward(chat_id=BIN_CHANNEL)

        # ───── Streaming control (info.py based) ─────
        stream_disabled = chat_id in NO_STREAM_CHANNELS

        raw_stream = (
            None if stream_disabled
            else f"{URL}watch/{msg.id}/ProBotz.mkv?hash={get_hash(msg)}"
        )
        raw_download = f"{URL}{msg.id}?hash={get_hash(msg)}"
        raw_file_link = f"https://t.me/{BOT_USERNAME}?start=file_{msg.id}"

        if IS_SHORTLINK:
            stream = None if stream_disabled else await get_shortlink(raw_stream)
            download = await get_shortlink(raw_download)
            file_link = await get_shortlink(raw_file_link)
        else:
            stream = raw_stream
            download = raw_download
            file_link = raw_file_link

        # ───── Log message ─────
        await msg.reply_text(
            text=(
                f"**Channel Name:** `{broadcast.chat.title}`\n"
                f"**CHANNEL ID:** `{broadcast.chat.id}`\n"
                f"**Request URL:** {download}"
            ),
            quote=True
        )

        # ───── Caption ─────
        new_caption = CHANNEL_FILE_CAPTION.format(CHANNEL, file_name)

        # ───── Buttons ─────
        buttons_list = []

        if not stream_disabled:
            buttons_list.append([
                InlineKeyboardButton(" ꜱᴛʀᴇᴀᴍ ", url=stream),
                InlineKeyboardButton(" ᴅᴏᴡɴʟᴏᴀᴅ ", url=download)
            ])
        else:
            buttons_list.append([
                InlineKeyboardButton(" ᴅᴏᴡɴʟᴏᴀᴅ ", url=download)
            ])

        buttons_list.append([
            InlineKeyboardButton(" ᴄʜᴇᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ғɪʟᴇ ", url=file_link)
        ])

        if IS_SHORTLINK:
            buttons_list.append([
                InlineKeyboardButton("• ʜᴏᴡ ᴛᴏ ᴏᴘᴇɴ •", url=HOW_TO_OPEN)
            ])

        buttons = InlineKeyboardMarkup(buttons_list)

        await bot.edit_message_caption(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            caption=new_caption,
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )

    # ───── Error handling ─────
    except asyncio.exceptions.TimeoutError:
        await asyncio.sleep(5)
        await channel_receive_handler(bot, broadcast)

    except FloodWait as w:
        await asyncio.sleep(w.value)

    except Exception as e:
        await bot.send_message(
            chat_id=BIN_CHANNEL,
            text=f"❌ **Error:** `{e}`",
            disable_web_page_preview=True
        )
        print(f"❌ Can't edit channel message! Error: {e}")
