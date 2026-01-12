import os, sys, glob, pytz, asyncio, logging, importlib
from pathlib import Path

from pyrogram import idle
import pyrogram.utils  # Import pyrogram.utils explicitly

# ================= EVENT LOOP FIX (FINAL & SAFE) =================
# Python 3.10+ compatible, no DeprecationWarning
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ================================================================

# Patch pyrogram.utils.get_peer_type to handle newer peer IDs
def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"

# Apply the patch
pyrogram.utils.get_peer_type = get_peer_type_new
pyrogram.utils.MIN_CHANNEL_ID = -1002822095763

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from info import *
from Script import script
from datetime import date, datetime
from aiohttp import web
from web import web_server, check_expired_premium
from web.server import StreamBot
from utils import Temp, ping_server
from web.server.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)

StreamBot.start()

async def start():
    print("\n")
    print("Initalizing Your Bot")

    await initialize_clients()

    for name in files:
        patt = Path(name)
        plugin_name = patt.stem.replace(".py", "")
        plugins_dir = Path(f"plugins/{plugin_name}.py")
        import_path = f"plugins.{plugin_name}"
        spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
        load = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(load)
        sys.modules[import_path] = load
        print("Imported => " + plugin_name)

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

    StreamBot.loop.create_task(check_expired_premium(StreamBot))

    await StreamBot.send_message(
        chat_id=LOG_CHANNEL,
        text=script.RESTART_TXT.format(today, time)
    )
    await StreamBot.send_message(
        chat_id=ADMINS[0],
        text="<b>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !!</b>"
    )
    await StreamBot.send_message(
        chat_id=SUPPORT_GROUP,
        text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>"
    )

    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    await idle()

if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info("----------------------- Service Stopped -----------------------")
