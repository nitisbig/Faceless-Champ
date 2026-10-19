"""Renderer-owned VTK process isolation for EGL interoperability.

Some VTK EGL initialization/finalization paths invalidate another library's EGL
display contexts in the same process. Rebinding cannot restore a destroyed
context. Keep VTK windows in a private interpreter, retaining the existing Core
raster producer, source clocks and bounded session cache. The pipe carries only
our own trusted Python snapshots; it is not an external serialization interface.
"""

import pickle
import struct
import subprocess
import sys
from collections import OrderedDict
from contextlib import suppress

_MAX_MESSAGE = 512 * 1024**2


def send(stream, value):
    data = pickle.dumps(value, protocol=5)
    if len(data) > _MAX_MESSAGE:
        raise ValueError("Arch snapshot exceeds the isolated renderer message budget")
    stream.write(struct.pack("!Q", len(data)))
    stream.write(data)
    stream.flush()


def receive(stream):
    def read(count):
        chunks = []
        while count:
            part = stream.read(count)
            if not part:
                raise EOFError("Isolated Arch renderer closed its pipe")
            chunks.append(part)
            count -= len(part)
        return b"".join(chunks)

    length = struct.unpack("!Q", read(8))[0]
    if length > _MAX_MESSAGE:
        raise ValueError("Arch response exceeds the isolated renderer message budget")
    return pickle.loads(read(length))


class ArchWorker:
    def __init__(self):
        self.process = subprocess.Popen(
            [sys.executable, "-m", __name__], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        self.known = set()

    def sprite(self, c, state, factor, age):
        from PIL import Image

        from ..arch import ArchDataError

        key = (c.fingerprint, c.width, c.height, c.source_start, str(c.font))
        try:
            send(self.process.stdin, (key, None if key in self.known else c, state, factor, age))
            reply = receive(self.process.stdout)
        except (EOFError, BrokenPipeError, OSError) as exc:
            raise ArchDataError("render", "Isolated VTK renderer exited; check offscreen EGL/OpenGL drivers") from exc
        if reply[0] == "error":
            raise ArchDataError("render", reply[1])
        _, size, data, keys = reply
        self.known = set(keys)
        return Image.frombytes("RGBA", size, data)

    def close(self):
        process = self.process
        if process.poll() is None:
            with suppress(BrokenPipeError, OSError):
                send(process.stdin, None)
        process.stdin.close()
        process.stdout.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    from ..renderer import PillowRenderer

    clips = OrderedDict()
    with PillowRenderer(1, frame_cache_mb=0, arch_session_limit=4) as renderer:
        while True:
            try:
                request = receive(sys.stdin.buffer)
            except EOFError:
                return
            if request is None:
                return
            key, c, state, factor, age = request
            try:
                if c is not None:
                    clips[key] = c
                clips.move_to_end(key)
                c = clips[key]
                image = renderer._sprite(c, state, factor, age)
                while len(clips) > 4:
                    clips.popitem(last=False)
                send(sys.stdout.buffer, ("ok", image.size, image.tobytes(), list(clips)))
            except Exception as exc:  # noqa: BLE001 - report native failures across the private process boundary
                send(sys.stdout.buffer, ("error", str(exc)))


if __name__ == "__main__":
    main()
