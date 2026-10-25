import asyncio
import logging

from info import API_ID, API_HASH, BOT_TOKEN, SLEEP_THRESHOLD
from pyrogram import Client
from web.utils.config_parser import TokenParser
from web.server import multi_clients, work_loads, StreamBot

log = logging.getLogger("clients")


async def initialize_clients():
    multi_clients[0] = StreamBot
    work_loads[0] = 0

    all_tokens = TokenParser().parse_from_env()

    # never start the main token (or a duplicate) twice - Telegram would fight over the session
    seen = {BOT_TOKEN.strip()}
    unique = {}
    for cid, token in all_tokens.items():
        t = token.strip()
        if t in seen:
            log.warning("MULTI_TOKEN%s duplicates another token - skipped", cid)
            continue
        seen.add(t)
        unique[cid] = t

    if not unique:
        log.warning("No additional clients found, using the default client only")
        return

    gate = asyncio.Semaphore(3)  # start 3 at a time: avoids auth flood limits

    async def start_client(client_id: int, token: str):
        for attempt in range(3):
            try:
                async with gate:
                    log.info("Starting extra client %s (try %s)...", client_id, attempt + 1)
                    client = Client(
                        name=f"RXClient_{client_id}",
                        api_id=API_ID,
                        api_hash=API_HASH,
                        bot_token=token,
                        sleep_threshold=SLEEP_THRESHOLD,
                        no_updates=True,
                        in_memory=True,
                    )
                    await client.start()
                return client_id, client
            except Exception as e:
                log.error("Failed to start client %s: %r", client_id, e)
                await asyncio.sleep(3 * (attempt + 1))
        return None

    results = await asyncio.gather(*[start_client(i, t) for i, t in unique.items()])

    for res in results:
        if res:
            cid, cli = res
            multi_clients[cid] = cli
            work_loads[cid] = 0

    if len(multi_clients) > 1:
        log.info("✅ Multi-client mode: %s bots active", len(multi_clients))
    else:
        log.warning("No additional clients were initialized, using the default client only.")
