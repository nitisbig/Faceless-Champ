"""Run short Colab CLI commands with private project state and a real deadline.

No sessions are allocated or stopped except by the explicit forwarded command.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path


def find_cli_python(explicit=None):
    if explicit:
        path = shutil.which(explicit) or explicit
        if not Path(path).is_file():
            raise RuntimeError(f"Colab Python interpreter does not exist: {explicit}")
        # Resolving this symlink would lose a virtualenv's bin/python identity.
        return str(Path(path).absolute())
    if importlib.util.find_spec("colab_cli") is not None:
        return sys.executable
    executable = shutil.which("colab")
    if not executable:
        raise RuntimeError("Install google-colab-cli first, or pass --cli-python.")
    with Path(executable).open(encoding="utf-8") as stream:
        header = stream.readline().strip()
    if not header.startswith("#!"):
        raise RuntimeError(
            "Cannot locate Colab's Python; pass --cli-python explicitly."
        )
    words = shlex.split(header[2:])
    if words and Path(words[0]).name == "env":
        words = words[1:]
        if words and words[0] == "-S":
            words = words[1:]
    if len(words) != 1:
        raise RuntimeError("Unsupported Colab launcher; pass --cli-python explicitly.")
    path = shutil.which(words[0]) or words[0]
    if not Path(path).is_file():
        raise RuntimeError("Colab's Python is missing; pass --cli-python explicitly.")
    return str(Path(path).absolute())


def invoke_cli(directory, arguments):
    from colab_cli import cli
    from colab_cli.common import state
    from colab_cli.history import HistoryLogger
    from colab_cli.state import SettingsStore

    os.umask(0o077)
    private = directory / "cli"
    private.mkdir(parents=True, exist_ok=True, mode=0o700)

    def configure_logging(*_):
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger("colab_cli.client").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    cli.setup_logging = configure_logging
    cli.auto_update.run_background_check = lambda: None
    state._history = HistoryLogger(str(private / "history"))
    state._settings_store = SettingsStore(str(private / "settings.json"))
    sys.argv = ["colab", "--config", str(private / "sessions.json"), *arguments]
    cli.main()
    return 0


def redact(value):
    value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+", "Bearer [redacted]", value)
    value = re.sub(
        r"(?i)([?&](?:colab-runtime-proxy-token|access_token|refresh_token|token)=)[^&\s\"']+",
        r"\1[redacted]",
        value,
    )
    for quote in ('"', "'"):
        key = rf"{quote}(?:access_token|refresh_token|colab-runtime-proxy-token|token){quote}"
        content = rf"{quote}(?:\\.|[^{quote}\\])*{quote}"
        value = re.sub(
            rf"(?i)({key}\s*:\s*){content}",
            rf"\1{quote}[redacted]{quote}",
            value,
        )
    return value


def stop_local_process(proc):
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif proc.poll() is None:
        proc.kill()
    return proc.communicate()


def main(arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if len(arguments) >= 2 and arguments[0] == "_worker":
        return invoke_cli(Path(arguments[1]), arguments[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument(
        "--deadline", type=float, default=60, help="local wall-clock seconds"
    )
    parser.add_argument("--cli-python", help="optional installed Colab CLI interpreter")
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="Colab arguments after --"
    )
    args = parser.parse_args(arguments)
    forwarded = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not forwarded:
        parser.error("provide a Colab command after --")
    if not math.isfinite(args.deadline) or args.deadline <= 0:
        parser.error("--deadline must be finite and positive")
    if any(value == "--config" or value.startswith("--config=") for value in forwarded):
        parser.error("use --state-dir instead of forwarding --config")
    try:
        python = find_cli_python(args.cli_python)
    except (OSError, RuntimeError) as exc:
        parser.exit(2, f"{exc}\n")
    directory = args.state_dir.expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    command = [
        python,
        str(Path(__file__).resolve()),
        "_worker",
        str(directory),
        *forwarded,
    ]
    proc = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=args.deadline)
    except subprocess.TimeoutExpired:
        stdout, stderr = stop_local_process(proc)
        sys.stdout.write(redact(stdout))
        sys.stderr.write(redact(stderr))
        print(
            f"Colab command exceeded {args.deadline:g}s; stopped only this local CLI "
            "process group. The remote VM/job was not stopped. Inspect saved status "
            "before retrying.",
            file=sys.stderr,
        )
        return 124
    except KeyboardInterrupt:
        stop_local_process(proc)
        print("Local CLI stopped; the remote VM/job was not stopped.", file=sys.stderr)
        return 130
    sys.stdout.write(redact(stdout))
    sys.stderr.write(redact(stderr))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
