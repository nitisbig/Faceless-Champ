"""Bounded pipe operations and shutdown for an owned subprocess.

A single worker keeps blocking pipe I/O off the caller thread, including on
platforms where selectors cannot watch anonymous pipes. Only one operation is
in flight; frames cannot accumulate behind a stalled encoder.
"""

import queue
import subprocess
import threading
import time
from concurrent.futures import CancelledError


class ProcessIO:
    def __init__(self, process, *, timeout=60, cancel=None):
        self.process, self.timeout, self.cancel = process, timeout, cancel
        self._tasks = queue.Queue(maxsize=1)
        self._closed = False
        self._thread = threading.Thread(target=self._run, daemon=True, name="faceless-champ-pipe")
        self._thread.start()

    def _run(self):
        while True:
            task = self._tasks.get()
            if task is None:
                return
            operation, done, result = task
            try:
                result.append((True, operation()))
            except BaseException as exc:  # noqa: BLE001 -- transport failures to the owning thread
                result.append((False, exc))
            finally:
                done.set()
            if self._closed:
                return

    def check_cancelled(self):
        if self.cancel is not None and self.cancel():
            raise CancelledError("Video export cancelled")

    def call(self, operation, *, timeout=None):
        if self._closed:
            raise RuntimeError("Process pipe session is closed")
        self.check_cancelled()
        done, result = threading.Event(), []
        timeout = self.timeout if timeout is None else timeout
        deadline = time.monotonic() + timeout
        self._tasks.put_nowait((operation, done, result))
        try:
            while not done.wait(min(0.05, max(0, deadline - time.monotonic()))):
                self.check_cancelled()
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Subprocess pipe operation exceeded {timeout:g} seconds")
            self.check_cancelled()
            success, value = result[0]
            if success:
                return value
            raise value
        except BaseException:
            self.close()
            raise

    def close(self):
        if self._closed:
            return
        self._closed = True
        process = self.process
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=0.5)
        finally:
            # Termination releases OS pipes before taking Python stream locks.
            try:
                self._tasks.put_nowait(None)
            except queue.Full:
                pass  # An unstarted operation will observe _closed on completion.
            self._thread.join(timeout=1)
            if not self._thread.is_alive():
                for stream in (process.stdin, process.stdout):
                    if stream is not None:
                        stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
