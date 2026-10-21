"""Byte accounting and renderer-owned source sessions."""

from collections import OrderedDict

from PIL.Image import Image


class ByteCache:
    """Renderer-owned LRU; oversized values are returned but never retained."""

    def __init__(self, limit):
        self.limit = limit
        self.bytes = 0
        self.items = OrderedDict()

    def get(self, key):
        item = self.items.get(key)
        if item is not None:
            self.items.move_to_end(key)
            return item[0]

    def put(self, key, value, cost):
        old = self.items.pop(key, None)
        if old:
            self.bytes -= old[1]
        if cost <= self.limit:
            while self.bytes + cost > self.limit:
                _, (_, removed) = self.items.popitem(last=False)
                self.bytes -= removed
            self.items[key] = (value, cost)
            self.bytes += cost
        return value

    def clear(self):
        self.items.clear()
        self.bytes = 0


class SourceSessions:
    """Bound decoded frames by bytes and native sessions by count.

    Native library allocations are session-owned, not included in decoded bytes.
    A failing open must clean its partial allocation; a failing frame closes its
    session here. Cached/returned images never share mutable storage with callers.
    """

    def __init__(self, *, cache_bytes=64 * 1024**2, session_limit=4):
        if isinstance(session_limit, bool) or not isinstance(session_limit, int) or session_limit < 1:
            raise ValueError("session_limit must be a positive integer")
        if cache_bytes < 0:
            raise ValueError("cache_bytes must be nonnegative")
        self.frames = ByteCache(cache_bytes)
        self.sessions = OrderedDict()
        self.session_limit = session_limit

    def frame(self, source, size, time):
        key = source.fingerprint, size, source.frame_key(time)
        cached = self.frames.get(key)
        if cached is not None:
            return cached.copy()
        session_key = id(source), size
        owned = self.sessions.pop(session_key, None)
        if owned is None:
            while len(self.sessions) >= self.session_limit:
                self.sessions.popitem(last=False)[1][1].close()
            owned = source, source.open(size)
        self.sessions[session_key] = owned
        try:
            result = owned[1].frame(time)
            if not isinstance(result, Image) or result.mode != "RGBA" or result.size != size:
                raise ValueError("RasterSession.frame must return an RGBA image at its opened size")
            result = result.copy()
            self.frames.put(key, result, size[0] * size[1] * 4)
            return result.copy()
        except BaseException:
            self.sessions.pop(session_key)[1].close()
            raise

    def close(self):
        error = None
        while self.sessions:
            try:
                self.sessions.popitem(last=False)[1][1].close()
            except Exception as exc:  # noqa: BLE001 -- close every owned session before propagating
                error = error or exc
        self.frames.clear()
        if error is not None:
            raise error
