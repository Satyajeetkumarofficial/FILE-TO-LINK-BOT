import logging
from pyrogram import Client, types
from typing import Union, Optional, AsyncGenerator
from info import *
from utils import Temp

# Logging Setup (Better)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
for mod in ["aiohttp", "pyrogram", "aiohttp.web"]:
    logging.getLogger(mod).setLevel(logging.ERROR)




class WebXBot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=WORKERS,
            plugins={"root": "plugins"},
            sleep_threshold=SLEEP_THRESHOLD,
        )

    async def set_self(self):
        Temp.BOT = self

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> AsyncGenerator["types.Message", None]:
        """
        Asynchronously iterate through messages in a chat.
        Uses batching with a max of 200 messages per request.
        """
        current = offset
        while current < limit:
            batch_size = min(200, limit - current)
            ids = list(range(current, current + batch_size))
            messages = await self.get_messages(chat_id, ids)

            if not messages:
                break

            for msg in messages:
                if msg:  # Skip None
                    yield msg

            current += batch_size  # Increment by batch length


# ✅ Global single client instance
StreamBot = WebXBot()

# ✅ Client management setup
multi_clients = {}
work_loads = {}
