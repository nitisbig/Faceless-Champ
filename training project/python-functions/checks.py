"""Structural and layout checks only: no media rendering or example execution."""

from __future__ import annotations

from scene import (
    BASIC_CODE,
    CANVAS_SIZE,
    CODE_SIZE,
    EDITOR_FULL,
    EDITOR_SCALE,
    EDITOR_SPLIT,
    EXAMPLES,
    PARAMETER_CODE,
    RESTORE_DURATION,
    RETURN_CODE,
    REUSE_CODE,
    SHRINK_DURATION,
    TERMINAL_BOX,
    TERMINAL_EXIT,
    TOTAL_DURATION,
    TYPING,
)

from faceless_champ import CodingChamp, Text


def check(video, report):
    """Inspect authored states, including motion midpoints, without producing frames."""
    video.build()
    if abs(video.duration - TOTAL_DURATION) > 1e-9:
        raise AssertionError(f"Expected 120 seconds, got {video.duration}")
    if video.audio or report["audio_tracks"] != 0:
        raise AssertionError("This tutorial must contain no audio")
    if (video.canvas.width, video.canvas.height) != CANVAS_SIZE:
        raise AssertionError("Expected a 1920×1080 authoring canvas")
    if EDITOR_SPLIT.right + 32 != TERMINAL_BOX.left:
        raise AssertionError("The split workspace must have a 32px window gap")
    if report["external_text"]:
        raise AssertionError("This design must contain no external text")

    entries = {entry.component.training_id: entry for entry in video.entries if hasattr(entry.component, "training_id")}
    for entry in video.entries:
        if isinstance(entry.component, Text):
            name = getattr(entry.component, "training_id", "")
            if name != "editor.heading" and not (name.startswith("terminal.") and name.endswith(".heading")):
                raise AssertionError("Only window labels may contain standalone text")
    # Include all authored boundaries and dense samples through every animation.
    samples = {0.0, TOTAL_DURATION - 1e-6}
    for entry in video.entries:
        samples.add(entry.start)
        if entry.end is not None:
            samples.add(entry.end)
        for track in entry.tracks:
            if not 0 <= track.start < track.start + track.duration <= TOTAL_DURATION + 1e-9:
                raise AssertionError("Animation extends outside the 120-second scene")
            samples.update(track.start + track.duration * step / 8 for step in range(9))

    def visible(entry, time):
        return all(
            ancestor.start <= time
            and (ancestor.end is None or time < ancestor.end)
            and ancestor.state_at(time)["opacity"] > 1e-6
            for ancestor in (entry, *entry.ancestors())
        )

    geometry_samples = 0
    measured = {}
    geometry_keys = ("position", "scale", "scale_x", "scale_y", "rotation", "width", "height", "stroke_width")
    for time in sorted(samples):
        for name, component in video.training_objects.items():
            entry = entries[name]
            if not component.training_check_bounds or not visible(entry, time):
                continue
            # Alpha/reveal changes do not affect measured bounds. Reuse each
            # geometry state instead of rasterizing identical large shapes.
            states = [ancestor.state_at(time) for ancestor in (entry, *entry.ancestors())]
            geometry_key = (name, tuple(tuple(state.get(key) for key in geometry_keys) for state in states))
            if geometry_key not in measured:
                measured[geometry_key] = video.bounds_at(component, time)
            bounds = measured[geometry_key]
            # Shapes reserve two antialias pixels; the full-screen face is
            # intentionally flush with the canvas and clips this padding.
            padding = 2.01 if name == "editor.face" else 1e-6
            if (
                bounds.left < -padding
                or bounds.top < -padding
                or bounds.right > 1920 + padding
                or bounds.bottom > 1080 + padding
            ):
                raise AssertionError(f"{name} exceeds the canvas at {time:g}s: {bounds}")
            geometry_samples += 1

    code_entries = {name: entries[f"code.{name}"] for name in ("basic", "parameters", "return")}
    for name, expected in (("basic", BASIC_CODE), ("parameters", PARAMETER_CODE), ("return", REUSE_CODE)):
        component = code_entries[name].component
        if not isinstance(component, CodingChamp) or component.code != expected:
            raise AssertionError(f"Unexpected code revision: {name}")
        if component.font_size != CODE_SIZE:
            raise AssertionError("Unexpected editor code size")
        # Constructing CodingChamp already validates all glyph/line extents.
        if component.bounds.right > EDITOR_FULL.right - 20:
            raise AssertionError("Code surface does not fit the full-screen editor")
        for track in code_entries[name].tracks:
            if track.property in {"scale", "scale_x", "scale_y"}:
                raise AssertionError("Code must inherit the editor's uniform scale")

    # A direct seek after every typing beat must give the exact intended prefix.
    for name, _, end, prefix in TYPING:
        entry = code_entries[name]
        state = entry.state_at(end)
        count = entry.component.visible_count(state["reveal"])
        if entry.component.code[:count] != prefix:
            raise AssertionError(f"Incorrect typewriter prefix for {name} at {end:g}s")

    run_events = {event["id"]: event for event in report["events"] if event["kind"] == "run"}
    for example in EXAMPLES:
        run = run_events[example.id]
        output = entries[f"terminal.{example.id}.output"]
        terminal = entries[f"terminal.{example.id}"]
        if output.component.code + "\n" != example.stdout:
            raise AssertionError(f"Terminal output differs from authored stdout: {example.id}")
        if visible(output, example.publish - 0.001):
            raise AssertionError("Output appears before the command completes")
        if not visible(output, example.publish + 0.2):
            raise AssertionError("Output is missing after the publish time")
        if visible(terminal, example.close + TERMINAL_EXIT + 0.001):
            raise AssertionError("Terminal remains visible after its outro")
        # The entire editor, including its code, must shrink as a single group.
        editor_entry = entries["editor"]
        for time in (run["start"], example.publish, example.close):
            face = video.bounds_at(video.training_objects["editor.face"], time)
            state = editor_entry.state_at(time)
            if abs(state["scale"] - EDITOR_SCALE) > 1e-6 or state["position"] != EDITOR_SPLIT.center:
                raise AssertionError("The complete editor is not in its scaled run position")
            if state["scale_x"] != 1 or state["scale_y"] != 1:
                raise AssertionError("Editor must preserve its aspect ratio")
            # Bounds include antialias/stroke padding around the window face.
            if face.right > TERMINAL_BOX.left - 20:
                raise AssertionError("Editor and terminal overlap during a run")
        panel_name = (
            "basic" if example.id == "define-call" else "parameters" if example.id == "parameters" else "return"
        )
        code_bounds = video.bounds_at(video.training_objects[f"code.{panel_name}"], example.publish)
        if code_bounds.right > EDITOR_SPLIT.right - 20:
            raise AssertionError("Scaled code extends beyond the run window")
        restored = editor_entry.state_at(example.close + TERMINAL_EXIT + RESTORE_DURATION + 0.001)
        if restored["scale"] != 1 or restored["position"] != EDITOR_FULL.center:
            raise AssertionError("Editor does not return to its full-screen scale and position")

    return_entry = code_entries["return"]
    prior = return_entry.component.visible_count(return_entry.state_at(92.5)["reveal"])
    if return_entry.component.code[:prior] != RETURN_CODE:
        raise AssertionError("The return example must remain intact before appending reuse")
    for event in report["events"]:
        if event["kind"] != "typing":
            continue
        for run in run_events.values():
            if event["start"] < run["end"] + RESTORE_DURATION and event["end"] > run["start"] - SHRINK_DURATION:
                raise AssertionError("Typing must happen only with the full-width editor")

    return {
        **report,
        "structural_check": "passed",
        "geometry_samples": geometry_samples,
        "measured_geometry_states": len(measured),
        "sample_times": len(samples),
        "code_revisions": 3,
        "terminal_runs": len(EXAMPLES),
        "effective_code_size_during_runs": CODE_SIZE * EDITOR_SCALE,
        "examples_executed": False,
        "media_rendered": False,
        "visual_review": "pending user render",
    }
