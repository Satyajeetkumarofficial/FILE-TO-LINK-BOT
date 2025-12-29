import os, sys, glob, pytz, asyncio, logging, importlib
from pathlib import Path
from datetime import date, datetime
from aiohttp import web

from pyrogram import idle
import pyrogram.utils

from info import *
from Script import script
from web import web_server, check_expired_premium
from web.server import StreamBot
from utils import Temp, ping_server
from web.server.clients import initialize_clients

# ────────────────── PYROGRAM PATCH ──────────────────

def get_peer_type_new(peer_id: int) -> str:
    peer_id = str(peer_id)
    if not peer_id.startswith("-"):
        return "user"
    elif peer_id.startswith("-100"):
        return "channel"
    return "chat"

pyrogram.utils.get_peer_type = get_peer_type_new
pyrogram.utils.MIN_CHANNEL_ID = -1002822095763

# ────────────────── LOGGING ──────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# ────────────────── PLUGINS ──────────────────

plugins = glob.glob("plugins/*.py")

# ────────────────── MAIN START ──────────────────

async def start():
    print("\nInitalizing Your Bot")

    # ✅ START BOT INSIDE EVENT LOOP
    await StreamBot.start()
    await initialize_clients()

    for file in plugins:
        name = Path(file).stem
        spec = importlib.util.spec_from_file_location(f"plugins.{name}", file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[f"plugins.{name}"] = mod
        print("Imported =>", name)

    if ON_HEROKU:
        asyncio.create_task(ping_server())

    me = await StreamBot.get_me()
    Temp.BOT = StreamBot
    Temp.ME = me.id
    Temp.U_NAME = me.username
    Temp.B_NAME = me.first_name

    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    asyncio.create_task(check_expired_premium(StreamBot))

    # ✅ SAFE SEND (no crash if empty)
    if LOG_CHANNEL:
        await StreamBot.send_message(
            LOG_CHANNEL,
            script.RESTART_TXT.format(today, time)
        )

    if ADMINS:
        await StreamBot.send_message(
            ADMINS[0],
            "<b>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !!</b>"
        )

    if SUPPORT_GROUP:
        await StreamBot.send_message(
            SUPPORT_GROUP,
            f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>"
        )

    # ───── WEB SERVER ─────
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    await idle()

# ────────────────── ENTRY POINT ──────────────────

if __name__ == "__main__":
    try:
        asyncio.run(start())   # ✅ FINAL FIX (NO WARNING)
    except KeyboardInterrupt:
        logging.info("----------------------- Service Stopped -----------------------")
