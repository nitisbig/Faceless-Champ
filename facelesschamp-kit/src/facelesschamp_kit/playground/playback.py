"""Random-access editor and three result canvases; never execute source here."""

from __future__ import annotations

import difflib
import json
import math
from dataclasses import asdict

from faceless_champ.components import Component, finite
from faceless_champ.typography import load_font
from PIL import Image, ImageDraw, ImageOps

from facelesschamp_kit.coding import CodeTheme, CodingChamp, draw_code
from facelesschamp_kit.playground.model import PlaygroundError, PlaygroundScript
from facelesschamp_kit.playground.prepare import PreparedPlayground


class EditTimeline:
    """Deterministic source edits. Deletes precede inserts within each changed span."""

    def __init__(self, script):
        self.script = PlaygroundScript.from_record(script.record())
        self._edits = []
        previous = {}
        for c in self.script.checkpoints:
            old, new = previous.get(c.active_file, ""), c.files[c.active_file]
            operations = []
            shift = 0
            for tag, a, b, x, y in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
                if tag == "equal":
                    continue
                pos = a + shift
                operations.append((pos, old[a:b], new[x:y]))
                shift += (y - x) - (b - a)
            self._edits.append((old, operations, sum(len(a) + len(b) for _, a, b in operations)))
            previous = dict(c.files)

    def layout_sample_times(self):
        """Check extrema around edits and line joins without retaining intermediate source copies."""
        for c, (_, operations, total) in zip(self.script.checkpoints, self._edits):
            yield c.edit_start
            yield c.edit_end
            if total == 0 or c.edit_start == c.edit_end:
                continue
            count = 0
            for _, removed, inserted in operations:
                for text in (removed[::-1], inserted):
                    for offset, char in enumerate(text):
                        if char in {"\n", "\r"}:
                            for step in (count + offset, count + offset + 1):
                                yield c.edit_start + (c.edit_end - c.edit_start) * step / total
                    count += len(text)
                    yield c.edit_start + (c.edit_end - c.edit_start) * count / total

    def state_at(self, time):
        time = finite(time, "time", 0)
        index = 0
        for i, c in enumerate(self.script.checkpoints):
            if time >= c.edit_start:
                index = i
        c = self.script.checkpoints[index]
        old, operations, total = self._edits[index]
        progress = (
            0
            if time < c.edit_start
            else 1
            if time >= c.edit_end
            else (time - c.edit_start) / (c.edit_end - c.edit_start)
        )
        remaining = math.floor(total * progress + 1e-9)
        source = old
        for pos, deleted, inserted in operations:
            n = min(remaining, len(deleted))
            source = source[: pos + len(deleted) - n] + source[pos + len(deleted) :]
            remaining -= n
            if n < len(deleted):
                break
            n = min(remaining, len(inserted))
            source = source[:pos] + inserted[:n] + source[pos:]
            remaining -= n
            if n < len(inserted):
                break
        if progress == 1:
            source = c.files[c.active_file]
        changed = []
        for tag, _, _, a, b in difflib.SequenceMatcher(
            None, old.splitlines(), source.splitlines(), autojunk=False
        ).get_opcodes():
            if tag != "equal":
                changed.extend(range(a + 1, b + 1))
        return {
            "checkpoint": c.id,
            "file": c.active_file,
            "source": source,
            "first_line": c.first_line,
            "changed_lines": tuple(changed),
            "progress": progress,
        }


class PlaygroundView(Component):
    """Base for fixed, time-seekable playground viewports."""

    def __init__(self, *, width, height, source_start=0, **kwargs):
        super().__init__(**kwargs)
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.source_start = finite(source_start, "source_start", 0)

    def frame_key(self, age):
        return self.source_start + age


class CodeEditor(PlaygroundView):
    def __init__(self, script, *, width=800, height=800, font_size=24, theme="midnight", **kwargs):
        super().__init__(width=width, height=height, **kwargs)
        self.timeline = EditTimeline(script)
        self.font_size = finite(font_size, "font_size", 12)
        self.theme = CodeTheme.named(theme) if isinstance(theme, str) else theme
        if not isinstance(self.theme, CodeTheme):
            raise TypeError("theme must be a named theme or CodeTheme")
        self._rows = max(1, int((height - max(42, self.font_size * 1.6) - 56) / (self.font_size * 1.45)))
        for c in self.timeline.script.checkpoints:
            if c.first_line > max(1, len(c.files[c.active_file].splitlines())):
                raise PlaygroundError("PLAYGROUND_LAYOUT", "first_line exceeds revision length", checkpoint=c.id)
        for time in self.timeline.layout_sample_times():
            self._panel(self.timeline.state_at(time))

    def _panel(self, state):
        lines = state["source"].splitlines(keepends=True)
        first = state["first_line"]
        excerpt = "".join(lines[first - 1 : first - 1 + self._rows])
        # A terminal newline is source data, not an additional visible line.
        count = len(excerpt.splitlines()) or 1
        highlighted = tuple(n - first + 1 for n in state["changed_lines"] if first <= n < first + count)
        extension = state["file"].rsplit(".", 1)[-1]
        language = {
            "py": "python",
            "html": "html",
            "htm": "html",
            "js": "javascript",
            "css": "css",
            "json": "json",
        }.get(extension, "text")
        try:
            return CodingChamp(
                excerpt,
                language=language,
                theme=self.theme,
                font_size=self.font_size,
                width=self.width,
                height=self.height,
                filename=state["file"],
                first_line=first,
                highlighted_lines=highlighted,
            )
        except ValueError as exc:
            raise PlaygroundError(
                "PLAYGROUND_LAYOUT", str(exc), checkpoint=state["checkpoint"], file=state["file"]
            ) from exc

    def frame_image(self, age, factor=1):
        from faceless_champ._rendering.raster import RasterPainter

        panel = self._panel(self.timeline.state_at(self.source_start + age))
        # Intermediate edit states are not retained in either sprite or token caches.
        with RasterPainter(code_cache_mb=0, source_cache_mb=0) as painter:
            return draw_code(panel, panel.state(), factor, painter)


def _text(draw, text, box, *, size=24, minimum=18, color="#E9EFF9", font_path=None):
    from facelesschamp_kit.coding import MONO_FONT

    left, top, right, bottom = box
    text = str(text)
    for n in range(round(size), round(minimum) - 1, -1):
        font = load_font(font_path or str(MONO_FONT), n)
        bounds = draw.multiline_textbbox((0, 0), text, font=font, spacing=6)
        if bounds[2] - bounds[0] <= right - left and bounds[3] - bounds[1] <= bottom - top:
            draw.multiline_text((left, top - bounds[1]), text, font=font, fill=color, spacing=6)
            return
    raise PlaygroundError(
        "PLAYGROUND_LAYOUT", "Canvas text does not fit at minimum size; enlarge canvas or simplify values"
    )


def _optional_theme(theme):
    if isinstance(theme, str):
        theme = CodeTheme.named(theme)
    if theme is not None and not isinstance(theme, CodeTheme):
        raise TypeError("theme must be a named theme, CodeTheme, or None")
    return theme


class PlaygroundCanvas(PlaygroundView):
    def __init__(self, prepared, *, width=800, height=620, font_size=24, minimum_font_size=18, theme=None, **kwargs):
        super().__init__(width=width, height=height, **kwargs)
        self.theme = _optional_theme(theme)
        self.prepared = prepared if isinstance(prepared, PreparedPlayground) else PreparedPlayground(prepared)
        self.font_size, self.minimum_font_size = (
            finite(font_size, "font_size", 12),
            finite(minimum_font_size, "minimum_font_size", 12),
        )
        if self.minimum_font_size > self.font_size:
            raise PlaygroundError("PLAYGROUND_LAYOUT", "minimum_font_size exceeds font_size")
        self.script = self.prepared.script
        self._results = self.prepared.results
        self._captures = {}
        if self.script.mode == "web":
            from facelesschamp_kit.web import WebCapture

            self._captures = {
                i: WebCapture(self.prepared.directory / r["capture"]) for i, r in enumerate(self._results)
            }
        for c in self.script.checkpoints:
            self.frame_image(c.publish - self.source_start)

    def state_at(self, time):
        index = next(
            (i for i in reversed(range(len(self._results))) if time >= self.script.checkpoints[i].publish),
            None,
        )
        if index is None:
            return None
        result = self._results[index]
        items = {item.id: asdict(item) for item in self.script.items}
        if result["exit_code"] == 0:
            for b in self.script.bindings:
                items[b.target][b.property] = result["values"][b.key]
        events = [
            asdict(e)
            for e in self.script.events
            if e.checkpoint == self.script.checkpoints[index].id and e.at <= time < e.at + e.duration
        ]
        return {"index": index, "items": items, "events": events, "result": result}

    def _boxes(self, items):
        flows = [i for i in items.values() if i["kind"] == "flow"]
        others = [i for i in items.values() if i["kind"] != "flow"]
        boxes = {}
        margin, gap = 20, 18
        top = margin
        if flows:
            width = (self.width - margin * 2 - gap * (len(flows) - 1)) / len(flows)
            height = min(100, self.height / 4)
            for i, item in enumerate(flows):
                x = margin + i * (width + gap)
                boxes[item["id"]] = (x, top, x + width, top + height)
            top += height + gap * 2
        columns = 2 if len(others) > 1 else 1
        rows = max(1, math.ceil(len(others) / columns))
        width = (self.width - margin * 2 - gap * (columns - 1)) / columns
        height = (self.height - top - margin - gap * (rows - 1)) / rows
        for i, item in enumerate(others):
            x, y = margin + (i % columns) * (width + gap), top + (i // columns) * (height + gap)
            boxes[item["id"]] = (x, y, x + width, y + height)
        if any(r - l < 80 or b - t < 70 for l, t, r, b in boxes.values()):
            raise PlaygroundError("PLAYGROUND_LAYOUT", "Too many items for canvas; enlarge it or split the scene")
        return boxes

    def frame_image(self, age, factor=1):
        time = self.source_start + age
        state = self.state_at(time)
        image = Image.new(
            "RGBA", (round(self.width), round(self.height)), self.theme.background if self.theme else "#101A2B"
        )
        draw = ImageDraw.Draw(image)
        if state is not None:
            result = state["result"]
            if result["exit_code"]:
                _text(
                    draw,
                    "Execution error\nSee output below",
                    (24, 24, self.width - 24, self.height - 24),
                    size=self.font_size,
                    minimum=self.minimum_font_size,
                    color="#FF9299",
                )
            elif self.script.mode == "web":
                checkpoint = self.script.checkpoints[state["index"]]
                capture = self._captures[state["index"]]
                frame = capture.image(max(0, time - checkpoint.publish))
                frame = ImageOps.contain(frame, image.size)
                image.alpha_composite(frame, ((image.width - frame.width) // 2, (image.height - frame.height) // 2))
            else:
                boxes = self._boxes(state["items"])
                for item in state["items"].values():
                    active = any(e["target"] == item["id"] or e["to"] == item["id"] for e in state["events"])
                    cells = [
                        tuple(e["cell"]) for e in state["events"] if e["target"] == item["id"] and e["cell"] is not None
                    ]
                    self._draw_item(draw, item, boxes[item["id"]], active, cells)
                for event in state["events"]:
                    if event["to"]:
                        a, b = boxes[event["target"]], boxes[event["to"]]
                        start, end = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2), ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
                        signal = self.theme.accent if self.theme else "#F5C86B"
                        draw.line((start, end), fill=signal, width=3)
                        t = (time - event["at"]) / event["duration"]
                        x, y = (u + (v - u) * t for u, v in zip(start, end))
                        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=signal)
        return image.resize(
            (max(1, round(self.width * factor)), max(1, round(self.height * factor))), Image.Resampling.LANCZOS
        )

    def _draw_item(self, draw, item, box, active, cells=()):
        l, t, r, b = box
        color = (self.theme.accent if self.theme else "#F5C86B") if active else item["color"]
        draw.rounded_rectangle(
            box, radius=12, fill=self.theme.chrome if self.theme else "#18263B", outline=color, width=4 if active else 2
        )

        def text(value, bounds, color=None):
            color = color or (self.theme.foreground if self.theme else "#E9EFF9")
            _text(draw, value, bounds, size=self.font_size, minimum=self.minimum_font_size, color=color)

        text(item["label"] or item["id"], (l + 14, t + 12, r - 14, t + 45), color)
        top = t + 56
        value, kind = item["value"], item["kind"]
        if kind == "car":
            cx = (l + r) / 2
            cy = top + 52
            half = min((r - l - 40) / 2, 110)
            car_color = item["color"]
            draw.polygon(
                [(cx - half * 0.7, cy), (cx - half * 0.4, cy - 35), (cx + half * 0.35, cy - 35), (cx + half * 0.7, cy)],
                fill=car_color,
            )
            draw.rounded_rectangle((cx - half, cy, cx + half, cy + 32), radius=9, fill=car_color)
            for x in (cx - half * 0.6, cx + half * 0.6):
                draw.ellipse((x - 15, cy + 20, x + 15, cy + 50), fill="#060B14", outline="#C6D3E5", width=3)
            top = cy + 68
        if kind in {"matrix", "vector"} and value is not None:
            rows = [value] if kind == "vector" else value
            cw, ch = (r - l - 28) / len(rows[0]), min(64, (b - top - 16) / len(rows))
            if cw < 40 or ch < 34:
                raise PlaygroundError("PLAYGROUND_LAYOUT", "Tensor cells too small; show a smaller tensor")
            for y, row in enumerate(rows):
                for x, cell in enumerate(row):
                    left, upper = l + 14 + x * cw, top + y * ch
                    draw.rectangle(
                        (left, upper, left + cw - 3, upper + ch - 3),
                        fill=(self.theme.highlight if self.theme else "#745A22")
                        if (y, x) in cells
                        else (self.theme.chrome if self.theme else "#253952"),
                        outline=color,
                    )
                    text(f"{cell:g}", (left + 5, upper + 4, left + cw - 8, upper + ch - 7))
        elif value is not None:
            if isinstance(value, dict):
                content = "\n".join(f"{key}: {v}" for key, v in value.items())
            else:
                content = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, str)) else str(value)
            text(content, (l + 14, top, r - 14, b - 14))


class PlaygroundOutput(PlaygroundView):
    def __init__(self, prepared, *, width=800, height=160, font_size=18, theme=None, **kwargs):
        super().__init__(width=width, height=height, **kwargs)
        self.theme = _optional_theme(theme)
        self.prepared = prepared if isinstance(prepared, PreparedPlayground) else PreparedPlayground(prepared)
        self.font_size = finite(font_size, "font_size", 12)
        self.script = self.prepared.script
        self._results = self.prepared.results
        self._captures = {}
        if self.script.mode == "web":
            from facelesschamp_kit.web import WebCapture

            self._captures = {
                i: WebCapture(self.prepared.directory / r["capture"]) for i, r in enumerate(self._results)
            }

    def frame_image(self, age, factor=1):
        from facelesschamp_kit.coding import MONO_FONT

        image = Image.new(
            "RGBA", (round(self.width), round(self.height)), self.theme.background if self.theme else "#080F1C"
        )
        draw = ImageDraw.Draw(image)
        font = load_font(str(MONO_FONT), round(self.font_size))
        time = self.source_start + age
        index = next(
            (i for i in reversed(range(len(self._results))) if time >= self.script.checkpoints[i].publish),
            None,
        )
        if index is not None:
            result = self._results[index]
            if self.script.mode == "web":
                capture = self._captures[index]
                source_time = max(0, time - self.script.checkpoints[index].publish)
                metadata = capture.metadata(source_time)
                stdout = "\n".join(capture.manifest.get("console", [])[: metadata.get("console_count", 0)])
                stderr = "\n".join(capture.manifest.get("errors", [])[: metadata.get("error_count", 0)])
            else:
                stdout, stderr = result["stdout"], result["stderr"]
            text = stdout + ("\n" if stdout and stderr else "") + stderr
            import textwrap

            columns = max(1, int((self.width - 24) / font.getlength("M")))
            lines = [
                piece for line in text.splitlines() for piece in (textwrap.wrap(line.expandtabs(4), columns) or [""])
            ]
            rows = max(1, int((self.height - 24) / (self.font_size * 1.5)))
            if len(lines) > rows:
                lines = ["… earlier output"] + lines[-max(0, rows - 1) :] if rows > 1 else [lines[-1]]
            draw.multiline_text(
                (12, 12),
                "\n".join(lines),
                font=font,
                fill="#FF9299" if result["exit_code"] else (self.theme.muted if self.theme else "#ADC4DC"),
                spacing=self.font_size * 0.5,
            )
        return image.resize(
            (max(1, round(self.width * factor)), max(1, round(self.height * factor))), Image.Resampling.LANCZOS
        )
