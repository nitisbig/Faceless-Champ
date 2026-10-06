"""Lower authoring records through public core APIs, with one master clock."""

from dataclasses import dataclass

from faceless_champ import Animation, Captions, FadeIn, Group, PopIn, Scene

from .assets import digest
from .blocks import BlockBuild
from .diagnostics import KitError


@dataclass
class CompiledVideo:
    composition: object
    report: dict
    context: object

    @property
    def duration(self):
        return self.composition.duration


def descendants(root):
    yield root
    if isinstance(root, Group):
        for child in root.children:
            yield from descendants(child)


def compile_video(video):
    ctx = video.context
    scene = Scene(ctx.canvas)
    if not video.segments:
        raise KitError("EMPTY_VIDEO", "Add at least one segment")
    visual_end = max(s.end for s in video.segments)
    duration = max(visual_end, video.voice.duration if video.voice else 0)
    final = max(video.segments, key=lambda s: (s.end, s.start))
    diagnostics, segment_reports, events = [], [], []
    claimed = set()
    hidden = set()
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
                bounds = placement.bounds or ctx.bounds
                built = placement.block(ctx, bounds) if placement.core else placement.block.compose(ctx, bounds)
                if not isinstance(built, BlockBuild):
                    built = BlockBuild(built) if placement.core else None
                if built is None:
                    raise KitError("BLOCK_CONTRACT", "compose must return BlockBuild")
                members = set(descendants(built.root))
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
                events.append((segment.start, 1, "add", built.root, None, scope))
                events.append((end, 0, "remove", built.root, None, scope))
                segment_reports[-1]["placements"].append(
                    {
                        "id": placement.handle.placement,
                        "bounds": {k: getattr(b, k) for k in ("left", "top", "right", "bottom")},
                        "children": list(built.children),
                        "z_index": placement.z_index,
                    }
                )
                if placement.enter:
                    run = placement.enter_duration or ctx.theme.motion_duration
                    if run > segment.duration:
                        raise KitError("MOTION_WINDOW", "Entry recipe exceeds segment; shorten enter_duration")
                    targets = (
                        list(built.root.children)
                        if placement.enter == "stagger" and isinstance(built.root, Group)
                        else [built.root]
                    )
                    step = run / (len(targets) + 1) if len(targets) > 1 else 0
                    leaf_duration = run - step * (len(targets) - 1)
                    for i, target in enumerate(targets):
                        recipe = PopIn if placement.enter == "pop" else FadeIn
                        animation = recipe(target)
                        hidden.add(target)
                        events.append((segment.start + i * step, 2, "play", animation, leaf_duration, scope))
            except KitError as exc:
                raise KitError(exc.code, exc.message, **(exc.scope | scope)) from exc
            except (ValueError, TypeError, OSError) as exc:
                raise KitError("BLOCK_BUILD", str(exc), **scope) from exc
        for target, factory, local, run in segment.motions:
            scope = {"segment": segment.name, "placement": target.placement}
            built = builds[target.placement]
            try:
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
        "narration": {
            "audio_checksum": digest(video.voice.audio),
            "subtitle_checksum": digest(video.voice.subtitles),
            "duration": video.voice.duration,
            "markers": video.voice.markers,
            "cues": [{"index": c.index, "start": c.start, "end": c.end} for c in video.voice.track.cues],
        }
        if video.voice
        else None,
    }
    return CompiledVideo(scene, report, ctx)
