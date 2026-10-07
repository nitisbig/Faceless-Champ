"""Callable templates; scaffolds remain editable copies owned by the user."""

from collections.abc import Mapping
from dataclasses import dataclass

from faceless_champ import Bounds, Canvas, Draw, linear

from .blocks import Comparison, Heading, MetricCard, StepList, WhiteboardDrawing
from .diagnostics import KitError, number
from .themes import WHITEBOARD, Theme
from .video import Video


@dataclass(frozen=True)
class WhiteboardScene:
    """One fresh board, timed with seconds or a pair of narration marker names."""

    name: str
    drawing: WhiteboardDrawing
    label: str | None = None
    duration: float | None = None
    start: float | None = None
    cues: tuple[str, str | None] | None = None

    def __post_init__(self):
        try:
            if not isinstance(self.name, str) or not self.name.strip() or "/" in self.name:
                raise KitError("SEGMENT_ID", "Scene names must be nonempty and cannot contain '/'")
            if not isinstance(self.drawing, WhiteboardDrawing):
                raise KitError("WHITEBOARD_SCENE", "drawing must be a WhiteboardDrawing")
            if self.label is not None and (not isinstance(self.label, str) or not self.label.strip()):
                raise KitError("WHITEBOARD_SCENE", "label must be nonempty text or None")
            if self.cues is not None:
                if self.duration is not None or self.start is not None:
                    raise KitError("SEGMENT_WINDOW", "Use cues or start/duration, not both")
                if not isinstance(self.cues, (tuple, list)) or len(self.cues) != 2:
                    raise KitError("CUE_WINDOW", "cues must contain a start marker and end marker (or None)")
                first, last = self.cues
                if (
                    not isinstance(first, str)
                    or not first
                    or (last is not None and (not isinstance(last, str) or not last))
                ):
                    raise KitError("CUE_MARKER", "Cue markers must be nonempty names")
                object.__setattr__(self, "cues", (first, last))
            else:
                object.__setattr__(self, "duration", number(self.duration, "duration", positive=True))
                if self.start is not None:
                    object.__setattr__(self, "start", number(self.start, "start"))
        except KitError as exc:
            raise KitError(exc.code, exc.message, **(exc.scope | {"segment": self.name})) from exc


@dataclass(frozen=True)
class _HiddenDrawing:
    drawing: WhiteboardDrawing

    def compose(self, context, bounds):
        built = self.drawing.compose(context, bounds)
        for child in built.children.values():
            child.opacity = 0
        return built


def _draw_stroke(component):
    animation = Draw(component)
    animation.targets["opacity"] = 1.0
    animation.starts["opacity"] = 1.0
    animation.rate_func = linear
    return animation


def whiteboard_basic(
    ctx,
    *,
    scenes,
    audio=None,
    subtitles=None,
    markers=None,
    captions=None,
    theme=None,
    draw_fraction=0.7,
):
    """Build an editable Video with ordered strokes, scene-local holds, and optional narration."""
    try:
        scenes = tuple(scenes)
    except TypeError:
        raise KitError("WHITEBOARD_SCENE", "scenes must be a nonempty sequence of WhiteboardScene recipes") from None
    if not scenes or any(not isinstance(scene, WhiteboardScene) for scene in scenes):
        raise KitError("WHITEBOARD_SCENE", "Supply at least one WhiteboardScene recipe")
    draw_fraction = number(draw_fraction, "draw_fraction", positive=True)
    if draw_fraction >= 1:
        raise KitError("WHITEBOARD_TIMING", "draw_fraction must be less than 1 to leave a completed-board hold")
    if captions is not None and not isinstance(captions, bool):
        raise KitError("WHITEBOARD_SCENE", "captions must be a boolean or None")
    has_narration = any(value is not None for value in (audio, subtitles, markers))
    if has_narration and (
        not isinstance(audio, str)
        or not audio
        or not isinstance(subtitles, str)
        or not subtitles
        or not isinstance(markers, Mapping)
        or not markers
    ):
        raise KitError("NARRATION", "Supply audio and subtitle asset IDs and a nonempty marker mapping together")
    selected_theme = WHITEBOARD if theme is None else theme
    if not isinstance(selected_theme, Theme):
        raise KitError("THEME", "theme must be a Theme instance")
    ctx.theme = selected_theme
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, selected_theme.background)
    if captions is not None:
        ctx.captions = captions
    video = Video(ctx)
    if has_narration:
        video.narration(audio=ctx.assets.audio(audio), subtitles=ctx.assets.subtitle(subtitles), markers=markers)
    previous_end = 0
    for recipe in scenes:
        try:
            if recipe.cues is not None:
                if video.voice is None:
                    raise KitError("NARRATION", "Cue-timed scenes require narration")
                segment = video.segment(recipe.name, window=video.voice.between(*recipe.cues))
            else:
                segment = video.segment(recipe.name, start=recipe.start, duration=recipe.duration)
            if segment.start < previous_end - 1e-9:
                raise KitError("WHITEBOARD_TIMING", "Recipe scenes must be in time order and cannot overlap")
            previous_end = segment.end
            area = ctx.bounds
            if recipe.label is not None:
                label_bottom = area.top + area.height * 0.15
                segment.add(
                    Heading(recipe.label),
                    id="label",
                    bounds=Bounds(area.left, area.top, area.right, label_bottom),
                    enter="fade",
                    enter_duration=min(ctx.theme.motion_duration, segment.duration * draw_fraction),
                )
                area = Bounds(area.left, label_bottom, area.right, area.bottom)
            drawing = segment.add(_HiddenDrawing(recipe.drawing), id="drawing", bounds=area)
            run = segment.duration * draw_fraction / len(recipe.drawing.drawings)
            for index in range(len(recipe.drawing.drawings)):
                segment.play(drawing[f"stroke-{index}"], _draw_stroke, at=index * run, duration=run)
        except KitError as exc:
            raise KitError(exc.code, exc.message, **(exc.scope | {"segment": recipe.name})) from exc
    return video


def silent(ctx, *, value=42, label="Reusable components"):
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        segment.add(MetricCard(value, label), enter="pop")
    with video.segment("comparison", duration=4) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", duration=3) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video


def narrated(ctx, *, audio="voiceover", subtitles="word_cues", markers=None):
    video = Video(ctx)
    if ctx.assets.entries.get(audio, {}).get("source") == "Synthetic demonstration speech":
        from faceless_champ import Bounds

        video.segment("sample-label", start=0, duration=30).add(
            Heading("SYNTHETIC DEMO AUDIO", variant="muted"),
            bounds=Bounds(64, 8, ctx.canvas.width - 64, 58),
            z_index=10001,
        )
    voice = video.narration(
        audio=ctx.assets.audio(audio),
        subtitles=ctx.assets.subtitle(subtitles),
        markers=markers or {"hook": 1, "comparison": 2, "finish": 3},
    )
    with video.segment("hook", window=voice.between("hook", "comparison")) as segment:
        segment.add(Heading("Build once. Reuse everywhere.", variant="accent"), enter="fade")
    with video.segment("comparison", window=voice.between("comparison", "finish")) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", window=voice.between("finish")) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
