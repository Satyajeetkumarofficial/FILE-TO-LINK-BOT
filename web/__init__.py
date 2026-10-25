from aiohttp import web
from .stream_routes import routes
from asyncio import sleep
from datetime import datetime, timedelta
from database.users_db import db
from info import PREMIUM_LOGS
from pyrogram import Client

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

REMINDER_TIMES = [
    ("1d", timedelta(days=1)),
    ("5h30m", timedelta(hours=5, minutes=30)),
    ("50m", timedelta(minutes=50))
]

async def check_expired_premium(client):
    while True:
        now = datetime.utcnow()
        expired_users = await db.get_expired(now)
        for user in expired_users:
            user_id = user["id"]
            await db.remove_premium_access(user_id)
            unset_flags = {f"reminder_{label}_sent": "" for label, _ in REMINDER_TIMES}
            await db.users.update_one({"id": user_id}, {"$unset": unset_flags})
            try:
                tg_user = await client.get_users(user_id)
                await client.send_message(
                    user_id,
                    f"<b>ʜᴇʏ {tg_user.mention},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ᴇxᴘɪʀᴇᴅ.\n\nTᴀᴘ /plan ꜰᴏʀ ʀᴇɴᴇᴡᴀʟ ᴏᴘᴛɪᴏɴs.</b>"
                )
                await client.send_message(
                    PREMIUM_LOGS,
                    f"<b>#Premium_Expired\nUser: {tg_user.mention}\nID: <code>{user_id}</code></b>"
                )
            except Exception as e:
                print(f"[EXPIRED ERROR] {e}")
            await sleep(0.5)
        for label, delta in REMINDER_TIMES:
            reminder_users = await db.get_expiring_soon(label, delta)
            for user in reminder_users:
                user_id = user["id"]
                try:
                    tg_user = await client.get_users(user_id)
                    await client.send_message(
                        user_id,
                        f"<b>ʜᴇʏ {tg_user.mention},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴡɪʟʟ ᴇxᴘɪʀᴇ ɪɴ {label}.\nTᴀᴘ /plan ᴛᴏ ʀᴇɴᴇᴡ ɴᴏᴡ!</b>"
                    )
                    await client.send_message(
                        PREMIUM_LOGS,
                        f"<b>#Reminder ({label})\nUser: {tg_user.mention}\nID: <code>{user_id}</code></b>"
                    )
                except Exception as e:
                    print(f"[REMINDER ERROR] {e}")
                await sleep(0.5)
        await sleep(60)
