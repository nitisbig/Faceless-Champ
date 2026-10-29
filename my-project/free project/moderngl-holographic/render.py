"""Holographic turbine CAD study; fifteen seconds, black, silent, graphics only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import moderngl
import numpy as np
from PIL import Image as PILImage

from faceless_champ import (
    Bloom,
    Canvas,
    EffectStack,
    ExportProgress,
    ExportSettings,
    GPUOptions,
    Image,
    Scene,
    create_renderer,
    render,
)

ROOT = Path(__file__).resolve().parent
DURATION = 15.0


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    scene.wait_until(DURATION)
    return scene


def camera(time, aspect):
    angle = -0.48 + time * 0.032
    eye = np.array([9.5 * math.sin(angle), 5.8, 9.5 * math.cos(angle)])
    target = np.array([0, 0.0, 0])
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    view = np.eye(4)
    view[:3, :3] = np.array([right, up, -forward])
    view[:3, 3] = -view[:3, :3] @ eye
    f = 1 / math.tan(math.radians(39) / 2)
    near, far = 0.1, 60.0
    projection = np.array(
        [
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
            [0, 0, -1, 0],
        ]
    )
    return (projection @ view).astype("f4")


def ease(value):
    value = np.clip(value, 0, 1)
    return float(value * value * (3 - 2 * value))


def cylinder(radius, height, nu=80, nv=12):
    def point(u, v):
        angle = u * math.tau
        r = radius * (1 + 0.035 * math.cos(v * math.tau))
        return (r * math.cos(angle), height * (v - 0.5), r * math.sin(angle))

    return surface(point, nu, nv)


def torus(radius, tube, nu=96, nv=8):
    def point(u, v):
        a, b = u * math.tau, v * math.tau
        return (
            (radius + tube * math.cos(b)) * math.cos(a),
            tube * math.sin(b),
            (radius + tube * math.cos(b)) * math.sin(a),
        )

    return surface(point, nu, nv)


def surface(point, nu, nv):
    records = []
    for j in range(nv):
        for i in range(nu):
            for di, dj in ((0, 0), (1, 0), (0, 1), (1, 0), (1, 1), (0, 1)):
                u, v = (i + di) / nu, (j + dj) / nv
                records.append((*point(u, v), u * nu, v * nv))
    return np.array(records, dtype="f4")


class HologramRenderer:
    """Project-local GL meshes → public FC Image → ModernGL Bloom/composition."""

    def __init__(self):
        self.native = create_renderer("moderngl", antialias=1, gpu=GPUOptions(frame_cache_mb=0))
        self.ctx = self.native.ctx
        self.resources, self.targets = [], []
        self.size = None
        try:
            vertex = (ROOT / "hologram.vert").read_text()
            fragment = (ROOT / "hologram.frag").read_text()
            with self.ctx:
                self.program = self.ctx.program(vertex_shader=vertex, fragment_shader=fragment)
                self.resources.append(self.program)
                self.meshes = {}
                for name, data in {
                    "housing": cylinder(1.33, 3.25, 64, 16),
                    "core": cylinder(0.36, 3.6, 24, 18),
                    "collar": torus(1.12, 0.12, 72, 6),
                    "rim": torus(1.34, 0.035, 96, 4),
                    "base": torus(1.85, 0.012, 128, 4),
                    "scan": cylinder(1.6, 0.016, 96, 1),
                    "blade": surface(
                        lambda u, v: (0.4 + u * 0.7, (v - 0.5) * 0.38 + u * 0.16, (v - 0.5) * 0.4 + u * u * 0.3), 5, 3
                    ),
                }.items():
                    vbo = self.ctx.buffer(data.tobytes())
                    vao = self.ctx.vertex_array(self.program, [(vbo, "3f 2f", "in_position", "in_grid")])
                    self.resources.extend([vbo, vao])
                    self.meshes[name] = vao
                lines = []

                def line(a, b):
                    lines.extend([(*a, 0, 0), (*b, 0, 0)])

                for index in range(-12, 13):
                    q = index * 0.4
                    line((q, -2.5, -4.8), (q, -2.5, 4.8))
                    line((-4.8, -2.5, q), (4.8, -2.5, q))
                for sign in (-1, 1):
                    x = sign * 2.25
                    line((x, -1.65, 0), (x, 1.65, 0))
                    for y in np.linspace(-1.65, 1.65, 23):
                        line((x - 0.06, y, 0), (x + 0.06, y, 0))
                    for y in (-1.65, 1.65):
                        line((sign * 1.5, y, 0), (x + sign * 0.15, y, 0))
                vbo = self.ctx.buffer(np.array(lines, dtype="f4").tobytes())
                self.lines = self.ctx.vertex_array(self.program, [(vbo, "3f 2f", "in_position", "in_grid")])
                self.resources.extend([vbo, self.lines])
            self.identity = {
                **self.native.identity,
                "hologram_shader_hash": hashlib.sha256((vertex + fragment).encode()).hexdigest(),
                "integration": "project-local GL meshes → public Image → ModernGL Bloom/composition",
            }
        except BaseException:
            self.close()
            raise

    def validate(self, scene):
        if scene.duration != DURATION:
            raise ValueError("Expected fifteen-second holographic scene")
        self.native.validate(scene)

    def draw(self, name, color, alpha=1, y=0, angle=0, scale=1, wire=1, x=0):
        c, s = math.cos(angle), math.sin(angle)
        model = np.array(
            [[c * scale, 0, s * scale, x], [0, scale, 0, y], [-s * scale, 0, c * scale, 0], [0, 0, 0, 1]], dtype="f4"
        )
        self.program["model"].write(model.T.copy().tobytes())
        self.program["color"].value = color
        self.program["opacity"].value = alpha
        self.program["wire_mode"].value = wire
        if name == "lines":
            self.lines.render(moderngl.LINES)
        else:
            self.meshes[name].render(moderngl.TRIANGLES)

    def frame(self, scene, time, size):
        if not math.isfinite(time) or not 0 <= time <= DURATION:
            raise ValueError("source time must be in [0, 15]")
        matrix = camera(time, size[0] / size[1])
        cyan, blue, white = (0.08, 0.68, 0.9), (0.08, 0.26, 0.55), (0.5, 0.91, 1.0)
        exploded = ease((time - 3.0) / 3) * (1 - ease((time - 11.5) / 2.5))
        with self.ctx:
            if self.size != size:
                for resource in reversed(self.targets):
                    resource.release()
                self.targets = []
                self.texture = self.ctx.texture(size, 4)
                self.targets.append(self.texture)
                self.fbo = self.ctx.framebuffer([self.texture])
                self.targets.append(self.fbo)
                self.size = size
            self.fbo.use()
            self.ctx.viewport = (0, 0, *size)
            self.ctx.enable_only(moderngl.BLEND)
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
            self.fbo.clear(0, 0, 0, 1)
            self.program["mvp"].write(matrix.T.copy().tobytes())
            self.program["time"].value = time
            self.program["reveal"].value = -2.8 + 6 * ease(time / 2)
            scan = -2.3 + ((time * 0.43) % 1.0) * 4.6
            self.program["scan_y"].value = scan
            self.draw("lines", blue, alpha=0.38, wire=0)
            for r in (1, 1.15, 1.36):
                self.draw("base", cyan, alpha=0.52, y=-2.46, scale=r)
            self.draw("core", white, alpha=0.7, angle=time * 0.25)
            for index in range(5):
                y = (index - 2) * (0.52 + exploded * 0.18)
                self.draw("collar", cyan, alpha=0.75, y=y, angle=-time * 0.1)
                for blade in range(12):
                    self.draw("blade", cyan, alpha=0.62, y=y, angle=blade * math.tau / 12 + time * 0.21, wire=1)
            for sign in (-1, 1):
                y = sign * (1.65 + 0.65 * exploded)
                self.draw("rim", white, alpha=0.9, y=y)
                self.draw("collar", cyan, alpha=0.65, y=y, scale=1.19)
            self.draw("housing", cyan, alpha=0.15 + 0.09 * (1 - exploded), angle=-time * 0.08)
            self.draw("scan", (0.12, 0.95, 0.78), alpha=0.8, y=scan, wire=0)
            pixels = self.fbo.read(components=4, alignment=1)
            self.ctx.disable(moderngl.BLEND)
        image = PILImage.frombytes("RGBA", size, pixels).transpose(PILImage.Transpose.FLIP_TOP_BOTTOM)
        # The additive viewport is opaque for the public composition bridge.
        image.putalpha(255)
        sampled = Scene(scene.canvas)
        sampled.add(
            Image.from_source(
                image,
                width=1920,
                height=1080,
                position=(960, 540),
                effects=EffectStack(bloom=Bloom(radius=12, threshold=0.42, intensity=0.8)),
            )
        )
        sampled.wait_until(DURATION)
        return self.native.frame(sampled, time, size)

    def close(self):
        with self.native.ctx:
            for resource in reversed(self.resources):
                resource.release()
            for resource in reversed(self.targets):
                resource.release()
        self.resources, self.targets = [], []
        self.native.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--preview", action="store_true", help="One-second scan sample at 7–8s")
    modes.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and (not math.isfinite(args.frame) or not 0 <= args.frame <= DURATION):
        parser.error("frame must be in [0, 15]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 15")
    if args.fps <= 0:
        parser.error("fps must be positive")
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "moderngl-holographic.mp4"
    )
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite")
    if output.suffix.lower() != (".png" if args.frame is not None else ".mp4"):
        parser.error("output must use .png for a frame or .mp4 for video")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    settings = ExportSettings(backend="moderngl", antialias=1, quality=args.quality, fps=args.fps)
    source_range = args.range or ([7, 8] if args.preview else [0, DURATION])
    with HologramRenderer() as renderer:
        print(json.dumps(renderer.identity), flush=True)
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            renderer.frame(scene, args.frame, settings.dimensions(scene.canvas)).convert("RGB").save(output)
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    renderer=renderer,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    overwrite=args.overwrite,
                    progress=progress,
                )
        evidence = {
            "scene_duration": scene.duration,
            "source_range": source_range,
            "dimensions": settings.dimensions(scene.canvas),
            "fps": args.fps if args.frame is None else None,
            "rendering": renderer.identity,
            "full_export_verified": False,
        }
    output.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
