"""Private killable browser preparation worker; invoked only by explicit preparation."""

import json
import sys
from pathlib import Path

from facelesschamp_kit.playground.model import PlaygroundScript
from facelesschamp_kit.web import HtmlPage, WebScript, capture_html


def main():
    directory = Path(sys.argv[1])
    request = json.loads((directory / "request.json").read_text())
    script = PlaygroundScript.from_record(request["script"])
    index = request["index"]
    checkpoint = script.checkpoints[index]
    end = script.checkpoints[index + 1].publish if index + 1 < len(script.checkpoints) else script.duration
    actions = checkpoint.web_script or WebScript(end - checkpoint.publish)
    if actions.duration < end - checkpoint.publish:
        raise ValueError("WebScript must cover the checkpoint output window")
    root = directory / "source"
    capture = capture_html(
        HtmlPage(root / checkpoint.entrypoint, viewport=script.viewport, asset_root=root, ready=checkpoint.ready),
        actions,
        fps=request["fps"],
        timeout=request["timeout"],
        cache_dir=directory / "capture",
        allow_errors=True,
        output_limit=request["output_limit"],
    )
    (directory / "response.json").write_text(json.dumps({"capture": str(capture.directory)}))


if __name__ == "__main__":
    main()
