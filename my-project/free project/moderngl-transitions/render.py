"""Cinematic equation-to-wave shader transition; fifteen seconds, black, silent."""

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
    """Column-vector perspective and a slow, restrained orbit."""
    angle = -0.55 + time * 0.055
    eye = np.array([8.5 * math.sin(angle), 5.6 + 0.3 * math.sin(time * 0.3), 8.5 * math.cos(angle)])
    forward = -eye / np.linalg.norm(eye)
    right = np.cross(forward, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    view = np.eye(4)
    view[:3, :3] = np.array([right, up, -forward])
    view[:3, 3] = -view[:3, :3] @ eye
    f = 1 / math.tan(math.radians(38) / 2)
    near, far = 0.1, 50.0
    projection = np.array(
        [
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
            [0, 0, -1, 0],
        ]
    )
    return (projection @ view).astype("f4"), tuple(eye)


class TransitionRenderer:
    """Deterministic GLSL particles/mesh/post pass, then public FC Image + Bloom."""

    def __init__(self):
        from PIL import ImageDraw, ImageFont

        self.native = create_renderer("moderngl", antialias=1, gpu=GPUOptions(frame_cache_mb=0))
        self.ctx = self.native.ctx
        self.resources, self.targets = [], []
        self.size = None
        try:
            # Rasterize only the mathematical source once; motion and effects run in GL.
            mask = PILImage.new("L", (1920, 1080))
            draw = ImageDraw.Draw(mask)
            font = ImageFont.truetype("DejaVuSerif.ttf", 112)
            small = ImageFont.truetype("DejaVuSerif.ttf", 92)
            draw.text((690, 462), "∂²u", font=font, fill=255, anchor="mm")
            draw.line((577, 535, 803, 535), fill=255, width=4)
            draw.text((690, 607), "∂t²", font=font, fill=255, anchor="mm")
            draw.text((1040, 540), "= c²∇²u", font=small, fill=255, anchor="mm")
            values = np.asarray(mask)
            y, x = np.nonzero(values[::2, ::2] > 100)
            x, y = x * 2, y * 2
            rng = np.random.default_rng(29)
            count = len(x)
            data = np.column_stack((x / 960 - 1, 1 - y / 540, rng.random((count, 3)))).astype("f4")
            shaders = {
                name: (ROOT / name).read_text()
                for name in ("particles.vert", "particles.frag", "wave.vert", "wave.frag", "post.vert", "post.frag")
            }
            with self.ctx:
                self.particle_program = self.ctx.program(
                    vertex_shader=shaders["particles.vert"], fragment_shader=shaders["particles.frag"]
                )
                self.resources.append(self.particle_program)
                vbo = self.ctx.buffer(data.tobytes())
                self.resources.append(vbo)
                self.particles = self.ctx.vertex_array(self.particle_program, [(vbo, "2f 3f", "origin", "seed")])
                self.resources.append(self.particles)
                self.wave_program = self.ctx.program(
                    vertex_shader=shaders["wave.vert"], fragment_shader=shaders["wave.frag"]
                )
                self.resources.append(self.wave_program)
                n = 180
                u, v = np.meshgrid(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1))
                grid = np.stack((u, v), axis=-1).astype("f4")
                j, i = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
                a = j * (n + 1) + i
                indices = np.stack((a, a + 1, a + n + 1, a + 1, a + n + 2, a + n + 1), axis=-1).astype("u4")
                vbo, ibo = self.ctx.buffer(grid.tobytes()), self.ctx.buffer(indices.tobytes())
                self.resources.extend((vbo, ibo))
                self.wave = self.ctx.vertex_array(self.wave_program, [(vbo, "2f", "in_uv")], ibo)
                self.resources.append(self.wave)
                self.post_program = self.ctx.program(
                    vertex_shader=shaders["post.vert"], fragment_shader=shaders["post.frag"]
                )
                self.resources.append(self.post_program)
                self.post = self.ctx.vertex_array(self.post_program, [])
                self.resources.append(self.post)
            self.identity = {
                **self.native.identity,
                "custom_shader_hash": hashlib.sha256("".join(shaders.values()).encode()).hexdigest(),
                "particle_count": count,
                "integration": "GLSL particles + displaced mesh + post → public FC Image + ModernGL Bloom",
            }
        except BaseException:
            self.close()
            raise

    def validate(self, scene):
        if scene.duration != DURATION:
            raise ValueError("Expected fifteen-second transition scene")
        self.native.validate(scene)

    def frame(self, scene, time, size):
        if not math.isfinite(time) or not 0 <= time <= DURATION:
            raise ValueError("source time must be in [0, 15]")
        matrix, _ = camera(time * 0.6, size[0] / size[1])
        with self.ctx:
            if self.size != size:
                for resource in reversed(self.targets):
                    resource.release()
                self.targets = []
                self.source = self.ctx.texture(size, 4)
                self.depth = self.ctx.depth_renderbuffer(size)
                self.source_fbo = self.ctx.framebuffer([self.source], self.depth)
                self.result = self.ctx.texture(size, 4)
                self.result_fbo = self.ctx.framebuffer([self.result])
                self.targets.extend((self.source, self.depth, self.source_fbo, self.result, self.result_fbo))
                self.size = size
            self.source_fbo.use()
            self.ctx.viewport = (0, 0, *size)
            self.source_fbo.clear(0, 0, 0, 1, depth=1)
            self.ctx.enable_only(moderngl.DEPTH_TEST)
            self.wave_program["time"].value = time
            self.wave_program["mvp"].write(matrix.T.copy().tobytes())
            self.wave.render(moderngl.TRIANGLES)
            self.ctx.enable_only(moderngl.BLEND | moderngl.PROGRAM_POINT_SIZE)
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)
            self.particle_program["time"].value = time
            self.particle_program["height"].value = float(size[1])
            self.particle_program["mvp"].write(matrix.T.copy().tobytes())
            self.particles.render(moderngl.POINTS)
            self.ctx.enable_only(0)
            self.result_fbo.use()
            self.source.use(0)
            self.post_program["source"].value = 0
            self.post_program["time"].value = time
            self.post_program["resolution"].value = size
            self.post.render(moderngl.TRIANGLES, vertices=3)
            pixels = self.result_fbo.read(components=4, alignment=1)
        image = PILImage.frombytes("RGBA", size, pixels).transpose(PILImage.Transpose.FLIP_TOP_BOTTOM)
        sampled = Scene(scene.canvas)
        sampled.add(
            Image.from_source(
                image,
                width=1920,
                height=1080,
                position=(960, 540),
                effects=EffectStack(bloom=Bloom(radius=14, threshold=0.45, intensity=0.65)),
            )
        )
        sampled.wait_until(DURATION)
        return self.native.frame(sampled, time, size)

    def close(self):
        with self.ctx:
            for resource in reversed(self.targets):
                resource.release()
            for resource in reversed(self.resources):
                resource.release()
        self.targets, self.resources = [], []
        self.native.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--preview", action="store_true", help="One-second dissolve sample at 5–6s")
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
        else "moderngl-transitions.mp4"
    )
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite")
    if output.suffix.lower() != (".png" if args.frame is not None else ".mp4"):
        parser.error("output must use .png for a frame or .mp4 for video")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    settings = ExportSettings(backend="moderngl", antialias=1, quality=args.quality, fps=args.fps)
    source_range = args.range or ([5, 6] if args.preview else [0, DURATION])
    with TransitionRenderer() as renderer:
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
