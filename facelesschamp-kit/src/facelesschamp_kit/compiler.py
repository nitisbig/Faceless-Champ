"""Lower authoring records through public core APIs, with one master clock."""

from dataclasses import dataclass, field

from faceless_champ import (
    Animation,
    Bounds,
    Captions,
    ChessChamp,
    FadeIn,
    FadeOut,
    Group,
    PopIn,
    Scene,
    SlideIn,
    SlideOut,
    dot_grid,
    smooth,
)
from faceless_champ.arch import ArchChamp, ArchDataError
from faceless_champ.flow import FlowChamp, FlowDataError
from faceless_champ.os_ui import OSClip

from .assets import digest
from .blocks import BlockBuild
from .diagnostics import KitError, number


@dataclass
class CompiledVideo:
    composition: object
    report: dict
    context: object
    _placements: list = field(default_factory=list, repr=False)

    @property
    def duration(self):
        return self.composition.duration

    def layout_at(self, time):
        """Conservative animated bounds, in master design pixels.

        Only placement lifetimes are filtered. Opacity and masks do not shrink
        bounds; intersections are review candidates, not collision proofs.
        Core-authored compositions without kit handles report no placements.
        """
        time = number(time, "time")
        if time >= self.duration:
            raise KitError("SAMPLE_TIME", "Sample before the end of the composition", source_time=time)
        rows = []
        for record in self._placements:
            if not record["start"] <= time < record["end"]:
                continue

            def bounds(component):
                box = self.composition.bounds_at(component, time)
                return {key: getattr(box, key) for key in ("left", "top", "right", "bottom")}

            rows.append(
                {
                    "id": record["id"],
                    "segment": record["segment"],
                    "start": record["start"],
                    "end": record["end"],
                    "bounds": bounds(record["root"]),
                    "children": {name: bounds(child) for name, child in record["children"].items()},
                }
            )
        return {"source_time": time, "conservative": True, "placements": rows}


def descendants(root):
    yield root
    if isinstance(root, Group):
        for child in root.children:
            yield from descendants(child)


def _flow_targets(root):
    return [component for component in descendants(root) if not isinstance(component, Group)]


def _flow_step(theme, window, count):
    return min(theme.motion_stagger, 0.35 * window / (count - 1)) if count > 1 else 0


def compile_video(video):
    ctx = video.context
    scene = Scene(ctx.canvas)
    if not video.segments:
        raise KitError("EMPTY_VIDEO", "Add at least one segment")
    visual_end = max(s.end for s in video.segments)
    duration = max(visual_end, video.voice.duration if video.voice else 0)
    final = max(video.segments, key=lambda s: (s.end, s.start))
    diagnostics, segment_reports, events = [], [], []
    chess_assets = {}
    arch_designs = []
    layout_records = []
    claimed = set()
    hidden = set()
    if ctx.theme.background_pattern == "dots":
        backdrop = dot_grid(
            Bounds(0, 0, ctx.canvas.width, ctx.canvas.height),
            color=ctx.theme.grid_color,
            spacing=ctx.theme.grid_spacing,
            radius=ctx.theme.grid_radius,
            z_index=-1_000_000,
        )
        run = min(ctx.theme.motion_duration, duration / 2)
        with scene.at(0):
            scene.add(backdrop)
            scene.play(FadeIn(backdrop), run_time=run)
        with scene.at(duration - run):
            scene.play(FadeOut(backdrop), run_time=run)
    if duration > visual_end:
        diagnostics.append({"code": "AUDIO_TAIL_HOLD", "segment": final.name, "seconds": duration - visual_end})
    for segment in video.segments:
        end = duration if segment is final else segment.end
        segment_reports.append(
            {
                "id": segment.name,
                "start": segment.start,
                "end": end,
                "authored_end": segment.end,
                "cues": list(segment.cues),
                "placements": [],
            }
        )
        builds = {}
        for placement in segment.placements:
            scope = {"segment": segment.name, "placement": placement.handle.placement}
            try:
                placement_start = segment.start + placement.at
                placement_end = placement_start + placement.duration if placement.duration is not None else end
                if placement.at >= segment.duration or placement_end > end + 1e-9:
                    raise KitError("PLACEMENT_WINDOW", "Placement exceeds segment")
                bounds = placement.bounds or ctx.bounds
                built = placement.block(ctx, bounds) if placement.core else placement.block.compose(ctx, bounds)
                if not isinstance(built, BlockBuild):
                    built = BlockBuild(built) if placement.core else None
                if built is None:
                    raise KitError("BLOCK_CONTRACT", "compose must return BlockBuild")
                members = set(descendants(built.root))
                authored_lifetime = (
                    placement.duration if placement.duration is not None else segment.duration - placement.at
                )
                entrance = ctx.theme.default_enter if placement.enter == "theme" else placement.enter
                outro = ctx.theme.default_exit if placement.exit == "theme" else placement.exit
                entry_run = (placement.enter_duration or ctx.theme.motion_duration) if entrance else 0
                exit_run = (placement.exit_duration or ctx.theme.motion_duration) if outro else 0
                if entry_run + exit_run > authored_lifetime + 1e-9:
                    raise KitError("MOTION_WINDOW", "Entrance and outro must fit without overlapping")
                for member in members:
                    if isinstance(member, ArchChamp):
                        arch_designs.append(
                            {
                                "fingerprint": member.fingerprint,
                                "meshes": {p.id: p.mesh.fingerprint for p in member.parts},
                            }
                        )
                        samples = {member.source_start, min(member.duration, member.source_start + authored_lifetime)}
                        for action in member.script.actions:
                            for sample in (action.at, action.at + action.duration / 2, action.at + action.duration):
                                if member.source_start <= sample <= member.source_start + authored_lifetime:
                                    samples.add(sample)
                        diagnostics.extend(
                            {
                                **item,
                                **scope,
                                "script_time": sample,
                                "source_time": placement_start + sample - member.source_start,
                            }
                            for sample in sorted(samples)
                            for item in member.diagnostics_at(sample)
                        )
                    if isinstance(member, FlowChamp):
                        diagnostics.extend({**item, **scope} for item in member.diagnostics)
                        samples = {member.source_start, min(member.duration, member.source_start + authored_lifetime)}
                        for action in member.script.actions:
                            for i in range(len(action.targets)):
                                start = action.at + i * action.options.get("stagger", 0)
                                for sample in (start, start + action.duration / 2, start + action.duration):
                                    if member.source_start <= sample <= member.source_start + authored_lifetime:
                                        samples.add(sample)
                        for sample in sorted(samples):
                            for item in member.diagnostics_at(sample):
                                diagnostics.append(
                                    {
                                        **item,
                                        **scope,
                                        "script_time": sample,
                                        "source_time": placement_start + sample - member.source_start,
                                    }
                                )
                    if isinstance(member, ChessChamp):
                        chess_assets[placement.handle.placement] = member.assets.checksums
                    if (
                        isinstance(member, (OSClip, ChessChamp, FlowChamp, ArchChamp))
                        and member.duration - member.source_start > authored_lifetime + 1e-9
                    ):
                        raise KitError("MOTION_WINDOW", "Script exceeds authored placement lifetime")
                if claimed & members or any(m in video._constructed for m in members):
                    raise KitError("OWNERSHIP", "Block/factory must return fresh component instances")
                if not set(built.children.values()) <= members:
                    raise KitError("BLOCK_CONTRACT", "Named children must belong to the root hierarchy")
                claimed.update(members)
                video._constructed.update(members)
                b = built.root.bounds
                if (
                    b.left < bounds.left - 1
                    or b.top < bounds.top - 1
                    or b.right > bounds.right + 1
                    or b.bottom > bounds.bottom + 1
                ):
                    raise KitError("LAYOUT", "Block exceeds allocated bounds; resize content or change its layout")
                built.root.z_index = placement.z_index
                builds[placement.handle.placement] = built
                layout_records.append(
                    {
                        "id": placement.handle.placement,
                        "segment": segment.name,
                        "start": placement_start,
                        "end": placement_end,
                        "root": built.root,
                        "children": built.children,
                    }
                )
                events.append((placement_start, 1, "add", built.root, None, scope))
                events.append((placement_end, 0, "remove", built.root, None, scope))
                segment_reports[-1]["placements"].append(
                    {
                        "id": placement.handle.placement,
                        "bounds": {k: getattr(b, k) for k in ("left", "top", "right", "bottom")},
                        "children": list(built.children),
                        "z_index": placement.z_index,
                        "start": placement_start,
                        "end": placement_end,
                        "enter": entrance,
                        "exit": outro,
                        "enter_duration": entry_run,
                        "exit_duration": exit_run,
                    }
                )
                if entrance:
                    run = entry_run
                    targets = (
                        _flow_targets(built.root)
                        if entrance == "flow"
                        else list(built.root.children)
                        if entrance == "stagger" and isinstance(built.root, Group)
                        else [built.root]
                    )
                    step = (
                        _flow_step(ctx.theme, run, len(targets))
                        if entrance == "flow"
                        else run / (len(targets) + 1)
                        if len(targets) > 1
                        else 0
                    )
                    leaf_duration = run - step * (len(targets) - 1)
                    for i, target in enumerate(targets):
                        if entrance == "flow":
                            animation = SlideIn(target, direction="up", distance=ctx.theme.motion_distance)
                            animation.starts["position"] = (
                                target.position[0],
                                target.position[1] + ctx.theme.motion_distance,
                            )
                            animation.targets["position"] = target.position
                            animation.relative = ()
                            animation.rate_func = smooth
                        else:
                            animation = (PopIn if entrance == "pop" else FadeIn)(target)
                        hidden.add(target)
                        events.append((placement_start + i * step, 2, "play", animation, leaf_duration, scope))
                if outro:
                    targets = list(reversed(_flow_targets(built.root))) if outro == "flow" else [built.root]
                    step = _flow_step(ctx.theme, exit_run, len(targets)) if outro == "flow" else 0
                    leaf_duration = exit_run - step * (len(targets) - 1)
                    for i, target in enumerate(targets):
                        animation = (
                            SlideOut(target, direction="up", distance=ctx.theme.motion_distance)
                            if outro == "flow"
                            else FadeOut(target)
                        )
                        if outro == "flow":
                            animation.rate_func = smooth
                        events.append((placement_end - exit_run + i * step, 2, "play", animation, leaf_duration, scope))
            except KitError as exc:
                raise KitError(exc.code, exc.message, **(exc.scope | scope)) from exc
            except (ValueError, TypeError, OSError) as exc:
                from faceless_champ import PlaygroundError

                if isinstance(exc, PlaygroundError):
                    raise KitError(exc.code, str(exc), **(exc.scope | scope)) from exc
                if isinstance(exc, FlowDataError):
                    raise KitError("FLOW_DATA", str(exc), path=exc.path, **scope) from exc
                if isinstance(exc, ArchDataError):
                    code = (
                        "ARCH_DEPENDENCY"
                        if exc.field == "dependency"
                        else "ARCH_RENDER"
                        if exc.field == "render"
                        else "ARCH_DATA"
                    )
                    raise KitError(code, str(exc), path=exc.field, **scope) from exc
                raise KitError("BLOCK_BUILD", str(exc), **scope) from exc
        for target, factory, local, run in segment.motions:
            scope = {"segment": segment.name, "placement": target.placement}
            built = builds[target.placement]
            try:
                placement = next(p for p in segment.placements if p.handle.placement == target.placement)
                motion_end = placement.at + placement.duration if placement.duration is not None else segment.duration
                if local < placement.at or local + run > motion_end + 1e-9:
                    raise KitError("MOTION_WINDOW", "Animation exceeds placement lifetime", **scope)
                component = built.children[target.child] if target.child is not None else built.root
                animation = factory(component)
                if not isinstance(animation, Animation) or animation.component is not component:
                    raise KitError("MOTION", "Animation callback must animate its supplied component", **scope)
            except KeyError:
                raise KitError("HANDLE", f"Unknown named child {target.child!r}", **scope) from None
            except (ValueError, TypeError, AttributeError) as exc:
                raise KitError("MOTION", str(exc), **scope) from exc
            events.append((segment.start + local, 2, "play", animation, run, scope))
    for time, _, kind, target, run, scope in sorted(events, key=lambda e: (e[0], e[1])):
        try:
            with scene.at(time):
                if kind == "add":
                    members = list(descendants(target))
                    saved = {c: c.opacity for c in members if c in hidden}
                    try:
                        for c in saved:
                            c.opacity = 0
                        scene.add(target)
                    finally:
                        for c, opacity in saved.items():
                            c.opacity = opacity
                elif kind == "remove":
                    scene.remove(target)
                else:
                    scene.play(target, run_time=run)
        except (ValueError, TypeError) as exc:
            raise KitError("TIMELINE", str(exc), **scope) from exc
    if video.voice:
        scene.add_audio(video.voice.audio, start=0)
        if ctx.captions and video.voice.track is None:
            raise KitError("NARRATION", "Captions require subtitles")
        if ctx.captions:
            caption = Captions(
                video.voice.track,
                width=ctx.canvas.width - 2 * ctx.safe_margin,
                font=ctx.theme.font,
                font_size=ctx.theme.body_size,
                color=ctx.theme.foreground,
                highlight_color=ctx.theme.accent,
                future_color=ctx.theme.muted,
                z_index=10000,
                position=(ctx.canvas.width / 2, ctx.canvas.height - ctx.safe_margin - ctx.caption_space / 2),
            )
            while (
                caption.bounds.height > ctx.caption_space
                or caption.bounds.width > ctx.canvas.width - 2 * ctx.safe_margin
            ):
                caption.font_size -= 2
                if caption.font_size < ctx.theme.minimum_font_size:
                    raise KitError(
                        "CAPTION_FIT", "Captions exceed their reserved area; shorten phrases or increase caption_space"
                    )
            with scene.at(0):
                scene.add(caption)
    scene.wait_until(duration)
    report = {
        "schema_version": 1,
        "authoring": "kit",
        "duration": duration,
        "segments": segment_reports,
        "diagnostics": diagnostics,
        "chess_assets": chess_assets,
        "arch_designs": arch_designs,
        "narration": {
            "audio_checksum": digest(video.voice.audio),
            "subtitle_checksum": digest(video.voice.subtitles) if video.voice.subtitles is not None else None,
            "duration": video.voice.duration,
            "markers": video.voice.markers,
            "cues": [{"index": c.index, "start": c.start, "end": c.end} for c in video.voice.track.cues]
            if video.voice.track is not None
            else [],
        }
        if video.voice
        else None,
    }
    return CompiledVideo(scene, report, ctx, layout_records)
