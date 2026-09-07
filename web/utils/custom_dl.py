import asyncio
import logging
from info import *
from typing import Dict, Union
from web.server import work_loads
from pyrogram import Client, utils, raw
from .file_properties import get_file_ids
from pyrogram.session import Session, Auth
from pyrogram.errors import AuthBytesInvalid
from web.server.exceptions import FIleNotFound
from pyrogram.file_id import FileId, FileType, ThumbnailSource


# --------------------------------------------------------------------------
# Patch: serialize Session.restart() per Session instance.
#
# Pyrogram's own internals (the recv_worker / send() error handling) call
# session.restart() automatically, as a fire-and-forget background task,
# whenever the underlying TCP connection drops (e.g. "Connection lost",
# "Broken pipe"). When several concurrent streams share one media Session
# for a DC and the connection dies, more than one of these internal
# restarts can fire for the *same* Session object at the same time. Two
# concurrent restarts both call stop() -> await recv_task while a fresh
# recv_worker is already waiting on the socket, producing:
#   RuntimeError: read() called while another coroutine is already
#   waiting for incoming data
# This happens inside Pyrogram's own code, not ours, so no amount of
# try/except in our streaming code can catch it. Wrapping restart() with
# a per-instance lock ensures at most one restart runs at a time for a
# given session, regardless of who triggers it.
# --------------------------------------------------------------------------
_original_session_restart = Session.restart


async def _locked_session_restart(self, *args, **kwargs):
    lock = self.__dict__.get("_custom_restart_lock")
    if lock is None:
        lock = asyncio.Lock()
        self.__dict__["_custom_restart_lock"] = lock
    async with lock:
        return await _original_session_restart(self, *args, **kwargs)


Session.restart = _locked_session_restart


class ByteStreamer:
    def __init__(self, client: Client):
        """A custom class that holds the cache of a specific client and class functions.
        attributes:
            client: the client that the cache is for.
            cached_file_ids: a dict of cached file IDs.
            cached_file_properties: a dict of cached file properties.

        functions:
            generate_file_properties: returns the properties for a media of a specific message contained in Tuple.
            generate_media_session: returns the media session for the DC that contains the media file.
            yield_file: yield a file from telegram servers for streaming.

        This is a modified version of the <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/telegram/utils/custom_download.py>
        Thanks to Eyaadh <https://github.com/eyaadh>
        """
        self.clean_timer = 30 * 60
        self.client: Client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        # One lock per DC so concurrent requests for the same file/DC can't
        # race to create/restart the media session at the same time.
        self._session_locks: Dict[int, asyncio.Lock] = {}
        asyncio.create_task(self.clean_cache())

    async def get_file_properties(self, id: int) -> FileId:
        """
        Returns the properties of a media of a specific message in a FIleId class.
        if the properties are cached, then it'll return the cached results.
        or it'll generate the properties from the Message ID and cache them.
        """
        if id not in self.cached_file_ids:
            await self.generate_file_properties(id)
            logging.debug(f"Cached file properties for message with ID {id}")
        return self.cached_file_ids[id]

    async def generate_file_properties(self, id: int) -> FileId:
        """
        Generates the properties of a media file on a specific message.
        returns ths properties in a FIleId class.
        """
        file_id = await get_file_ids(self.client, BIN_CHANNEL, id)
        logging.debug(f"Generated file ID and Unique ID for message with ID {id}")
        if not file_id:
            logging.debug(f"Message with ID {id} not found")
            raise FIleNotFound
        self.cached_file_ids[id] = file_id
        logging.debug(f"Cached media message with ID {id}")
        return self.cached_file_ids[id]

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        """
        Generates the media session for the DC that contains the media file.
        This is required for getting the bytes from Telegram servers.

        Guarded by a per-DC lock: without this, several concurrent Range
        requests (e.g. a video player buffering) can all see no cached
        session at once and each start a brand new Session/recv_worker for
        the same DC. The losing sessions never get stopped, and a later
        restart on one of them races with a recv_worker that's still
        blocked reading on the old connection, producing:
        "RuntimeError: read() called while another coroutine is already
        waiting for incoming data".
        """
        lock = self._session_locks.setdefault(file_id.dc_id, asyncio.Lock())

        async with lock:
            media_session = client.media_sessions.get(file_id.dc_id, None)

            if media_session is None:
                if file_id.dc_id != await client.storage.dc_id():
                    media_session = Session(
                        client,
                        file_id.dc_id,
                        await Auth(
                            client, file_id.dc_id, await client.storage.test_mode()
                        ).create(),
                        await client.storage.test_mode(),
                        is_media=True,
                    )
                    await media_session.start()

                    for _ in range(6):
                        exported_auth = await client.invoke(
                            raw.functions.auth.ExportAuthorization(dc_id=file_id.dc_id)
                        )

                        try:
                            await media_session.send(
                                raw.functions.auth.ImportAuthorization(
                                    id=exported_auth.id, bytes=exported_auth.bytes
                                )
                            )
                            break
                        except AuthBytesInvalid:
                            logging.debug(
                                f"Invalid authorization bytes for DC {file_id.dc_id}"
                            )
                            continue
                    else:
                        await media_session.stop()
                        raise AuthBytesInvalid
                else:
                    media_session = Session(
                        client,
                        file_id.dc_id,
                        await client.storage.auth_key(),
                        await client.storage.test_mode(),
                        is_media=True,
                    )
                    await media_session.start()
                logging.debug(f"Created media session for DC {file_id.dc_id}")
                client.media_sessions[file_id.dc_id] = media_session
            else:
                logging.debug(f"Using cached media session for DC {file_id.dc_id}")
            return media_session

    async def _drop_media_session(self, client: Client, dc_id: int) -> None:
        """
        Removes a broken media session so the next request builds a fresh
        one, instead of every subsequent request reusing a dead connection.
        """
        lock = self._session_locks.setdefault(dc_id, asyncio.Lock())
        async with lock:
            session = client.media_sessions.pop(dc_id, None)
            if session is not None:
                try:
                    await session.stop()
                except Exception:
                    logging.debug(f"Error while stopping broken session for DC {dc_id}", exc_info=True)

    @staticmethod
    async def get_location(file_id: FileId) -> Union[
        raw.types.InputPhotoFileLocation,
        raw.types.InputDocumentFileLocation,
        raw.types.InputPeerPhotoFileLocation,
    ]:
        """
        Returns the file location for the media file.
        """
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        return location

    # How many GetFile requests to keep in flight at once per stream.
    # Higher = more throughput (multiple 1MB chunks requested in parallel
    # instead of one round-trip at a time), but too high can trigger
    # Telegram flood limits on very slow/free hosts. 4-6 is a safe,
    # noticeably faster default; tune via PREFETCH_WINDOW in info.py if needed.
    PREFETCH_WINDOW = int(globals().get("PREFETCH_WINDOW", 8))

    async def yield_file(
        self,
        file_id: FileId,
        index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ) -> Union[str, None]:
        """
        Custom generator that yields the bytes of the media file.
        Modded from <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/telegram/utils/custom_download.py#L20>
        Thanks to Eyaadh <https://github.com/eyaadh>

        Speed note: instead of awaiting one GetFile round-trip at a time
        (request -> wait -> request -> wait ...), this keeps a sliding
        window of several requests in flight concurrently and yields the
        results strictly in order. Chunks still arrive to the client in the
        correct sequence, but network round-trip latency is hidden behind
        the parallel in-flight requests, which noticeably raises effective
        throughput per stream.
        """
        client = self.client
        work_loads[index] += 1
        logging.debug(f"Starting to yielding file with client {index}.")
        media_session = await self.generate_media_session(client, file_id)
        location = await self.get_location(file_id)

        offsets = [offset + i * chunk_size for i in range(part_count)]
        window = max(1, self.PREFETCH_WINDOW)

        async def fetch(off: int) -> bytes:
            r = await media_session.send(
                raw.functions.upload.GetFile(location=location, offset=off, limit=chunk_size)
            )
            return r.bytes if isinstance(r, raw.types.upload.File) else b""

        pending: Dict[int, asyncio.Task] = {}
        next_to_fetch = 0
        next_to_yield = 0

        def _fill_pipeline():
            nonlocal next_to_fetch
            while next_to_fetch < len(offsets) and len(pending) < window:
                pending[next_to_fetch] = asyncio.create_task(fetch(offsets[next_to_fetch]))
                next_to_fetch += 1

        try:
            _fill_pipeline()
            while next_to_yield < len(offsets):
                task = pending.pop(next_to_yield)
                chunk = await task
                _fill_pipeline()

                if not chunk:
                    break

                current_part = next_to_yield + 1
                if part_count == 1:
                    yield chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    yield chunk[first_part_cut:]
                elif current_part == part_count:
                    yield chunk[:last_part_cut]
                else:
                    yield chunk

                next_to_yield += 1
        except (TimeoutError, AttributeError):
            pass
        except (ConnectionError, OSError, RuntimeError) as e:
            # The underlying connection/session is in a bad state (e.g. the
            # "read() called while another coroutine is already waiting"
            # race, or a dropped socket). Drop it so the next request
            # rebuilds a fresh session instead of reusing a dead one.
            logging.warning(f"Media session for DC {file_id.dc_id} appears broken, dropping it: {e}")
            await self._drop_media_session(client, file_id.dc_id)
        finally:
            for t in pending.values():
                t.cancel()
            logging.debug(f"Finished yielding file, served up to part {next_to_yield}.")
            work_loads[index] -= 1

    async def clean_cache(self) -> None:
        """
        function to clean the cache to reduce memory usage
        """
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
            logging.debug("Cleaned the cache")

        
