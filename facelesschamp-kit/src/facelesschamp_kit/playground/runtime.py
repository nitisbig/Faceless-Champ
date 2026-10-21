"""Explicit JSON emissions from trusted checkpoint programs (no automatic tracing)."""

import json
import os


def inputs():
    """Return this checkpoint's declared JSON inputs."""
    return json.loads(os.environ.get("FACELESS_PLAYGROUND_INPUTS", "{}"))


def _write(record):
    path = os.environ.get("FACELESS_PLAYGROUND_EMIT")
    if path is None:
        raise RuntimeError("emit/event require prepare_playground execution")
    text = json.dumps(record, allow_nan=False) + "\n"
    limit = int(os.environ["FACELESS_PLAYGROUND_LIMIT"])
    if len(text.encode()) + os.path.getsize(path) > limit:
        raise RuntimeError("Playground emission exceeds output limit")
    with open(path, "a", encoding="utf-8") as stream:
        stream.write(text)


def emit(key, value):
    """Publish a unique named JSON value for canvas bindings."""
    if not isinstance(key, str) or not key:
        raise ValueError("emit key must be nonempty text")
    _write({"kind": "value", "name": key, "value": value})


def event(name, payload=None):
    """Publish a named event; its video time is authored with EventBinding."""
    if not isinstance(name, str) or not name:
        raise ValueError("event name must be nonempty text")
    _write({"kind": "event", "name": name, "value": payload})
