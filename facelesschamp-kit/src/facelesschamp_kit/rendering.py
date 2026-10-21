"""Production operations over an already compiled video; no factories or policy."""

import math
from contextlib import contextmanager
from dataclasses import asdict

from faceless_champ import ExportProgress, create_renderer, render, render_storyboard, rendering_identity, save_frame
from faceless_champ.audio import probe as media_probe

__all__ = ["ExportProgress", "media_probe", "validate_rendering"]


@contextmanager
def _session(backend, antialias, gpu, renderer):
    if renderer is not None:
        yield renderer
    else:
        with create_renderer(backend, antialias=antialias, gpu=gpu) as owned:
            yield owned


def validate_rendering(compiled, settings, *, renderer=None):
    """Validate and resolve provenance, closing only a renderer owned here."""
    settings.dimensions(compiled.composition.canvas)
    with _session(settings.backend, settings.antialias, settings.gpu, renderer) as active:
        active.validate(compiled.composition)
        return rendering_identity(settings.backend, compiled.composition, renderer=active)


def frame(compiled, time, *, size, backend="pillow", antialias=1, gpu=None, renderer=None):
    """Return a PIL image at master time; the caller owns the returned image."""
    node = compiled.composition
    if (
        isinstance(time, bool)
        or not isinstance(time, (int, float))
        or not math.isfinite(time)
        or not 0 <= time < node.duration
    ):
        raise ValueError("Sample time must be finite and satisfy 0 <= time < duration")
    if len(size) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in size):
        raise ValueError("Frame size must contain two positive integers")
    if abs(size[0] / size[1] - node.canvas.aspect_ratio) > 2 / min(size):
        raise ValueError("Frame dimensions must preserve the canvas aspect ratio")
    with _session(backend, antialias, gpu, renderer) as active:
        active.validate(node)
        return active.frame(node, time, size).copy()


def _result(compiled, active, backend, output, settings, source_range=None):
    # Native sessions may discard driver/device information on close.
    return {
        "output": output,
        "rendering": rendering_identity(backend, compiled.composition, renderer=active),
        "source_range": source_range,
        "settings": settings,
    }


def save(compiled, time, output, *, size, backend="pillow", antialias=1, gpu=None, renderer=None, overwrite=False):
    with _session(backend, antialias, gpu, renderer) as active:
        path = save_frame(compiled.composition, time, output, size=size, renderer=active, overwrite=overwrite)
        return _result(
            compiled, active, backend, path, {"size": list(size), "antialias": antialias, "backend": backend}
        )


def storyboard(
    compiled,
    samples,
    directory,
    *,
    size=None,
    columns=3,
    backend="pillow",
    antialias=1,
    gpu=None,
    renderer=None,
    overwrite=False,
):
    samples = tuple(samples)
    with _session(backend, antialias, gpu, renderer) as active:
        path = render_storyboard(
            compiled.composition, samples, directory, size=size, columns=columns, renderer=active, overwrite=overwrite
        )
        effective_size = size or (480, max(1, round(480 / compiled.composition.canvas.aspect_ratio)))
        return _result(
            compiled,
            active,
            backend,
            path,
            {
                "size": list(effective_size),
                "columns": min(columns, len(samples)),
                "antialias": antialias,
                "backend": backend,
            },
        )


def export(
    compiled,
    output,
    *,
    settings,
    start_time=0,
    end_time=None,
    progress=None,
    renderer=None,
    overwrite=False,
    cancel=None,
):
    with _session(settings.backend, settings.antialias, settings.gpu, renderer) as active:
        path = render(
            compiled.composition,
            output,
            settings=settings,
            start_time=start_time,
            end_time=end_time,
            progress=progress,
            renderer=active,
            overwrite=overwrite,
            cancel=cancel,
        )
        effective = asdict(settings)
        effective["width"], effective["height"] = settings.dimensions(compiled.composition.canvas)
        return _result(
            compiled,
            active,
            settings.backend,
            path,
            effective,
            [start_time, compiled.duration if end_time is None else end_time],
        )
