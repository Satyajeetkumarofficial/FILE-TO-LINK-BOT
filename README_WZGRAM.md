# File-to-Link Bot — wzgram edition

## What changed
- **wzgram** instead of Pyrofork (`compat_pyrogram.py` makes `import pyrogram` work either way), uvloop enabled.
- **New streaming engine** (`web/utils/custom_dl.py`)
  - parts are striped across all bots (`MULTI_TOKEN*`) so every bot downloads at the same time
  - lanes per stream shrink automatically when many users stream (fair sharing, stable under load)
  - every Telegram call retries: FloodWait, timeouts, 5xx, dead session, expired file reference
  - a stream that cannot be completed is **aborted** (client resumes with Range) instead of silently truncated
  - bounded RAM, circuit breaker for a bad bot, `Client.stream_media()` fallback if the raw path ever breaks
- **Web layer** (`web/stream_routes.py`): max concurrent streams + per-IP cap + queue (503/429 with Retry-After instead of crashing), HEAD without Telegram traffic, `bytes=-N` ranges, correct chunk count, Mongo settings cache, `/health` and richer `/` status.
- Fixes: string env flags (`FSUB=False` really disables), no crash on missing optional IDs, wrong 404/403 mapping, page view no longer downloads the file from itself, `asyncio` import in private_stream, `FloodWait.x`, startup no longer dies if a log channel is invalid.

## Deploy checklist
1. `pip install -r requirements.txt` (or use the Dockerfile).
2. Required env: `API_ID API_HASH BOT_TOKEN BIN_CHANNEL DATABASE_URI FQDN` (+ `ADMINS`, channels as before).
3. **Speed:** add 3-4 extra bots as `MULTI_TOKEN1..4` and make **every one an admin of BIN_CHANNEL**.
4. Host as close to Telegram DCs as possible (Europe / Singapore) and with real bandwidth; a 0.1 vCPU free instance will be the limit.

## Tuning (all optional env vars)
| var | default | meaning |
|---|---|---|
| `PREFETCH_WINDOW` | 5 | GetFile requests in flight per bot (4-8) |
| `MAX_PARALLEL_CLIENTS` | 4 | bots used for one stream when the server is idle |
| `MAX_CONCURRENT_STREAMS` | 40 | open streams; extra users wait `STREAM_QUEUE_TIMEOUT`s then get 503 |
| `MAX_STREAMS_PER_IP` | 0 (off) | per-IP parallel connections; leave off behind Cloudflare/proxy |
| `LOG_REQUESTS` | errors | `errors` = log only status>=400, `all`, or `off` |
| `MAX_INFLIGHT_CHUNKS` | 64 | HARD RAM budget (MB) for stream buffers; streams wait/503 when it is used up |
| `FETCH_RETRIES` / `FETCH_TIMEOUT` | 5 / 30 | per-chunk retries / seconds |
| `MAX_REQUESTS_PER_CLIENT` | 16 | max parallel GetFile per bot; auto-shrinks on FloodWait, grows back slowly |
| `MIN_REQUESTS_PER_CLIENT` | 3 | lowest value the limit may shrink to |
| `FLOOD_BUDGET` | 90 | seconds a chunk may wait out FloodWaits before the stream is aborted |
| `WORKERS` | 50 | bot handler concurrency |

Small host (512 MB, e.g. Koyeb free): keep the defaults and use only **2-3 extra bots** (each bot costs RAM).
Big host: raise `MAX_INFLIGHT_CHUNKS` (e.g. 256) and `MAX_CONCURRENT_STREAMS`.

## Logins are stored in MongoDB (collection `bot_sessions`)
Restarts/redeploys/OOM-kills reuse the stored login, so Telegram's `FLOOD_WAIT ... auth.ImportBotAuthorization`
(crash-loop after many fresh logins) no longer happens. If a login FloodWait does occur the web server stays up and
the bot waits it out. Treat that collection like a password (anyone with it can act as your bots).

## Testing
- `python tests/test_engine.py` — engine test against a mock Telegram (correct bytes, ranges, errors, 80 users, disconnects, leaks).
- `python speedtest.py "<your stream link>" -c 1 4 8 -s 100` — real MB/s on your deployment.
