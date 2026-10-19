"""Ray-marched SDF morphs; fifteen seconds, black, silent, graphics only."""

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


class RaymarchRenderer:
    """Project-local SDF shader through the public FC Image/compositor bridge."""

    def __init__(self):
        self.native = create_renderer("moderngl", antialias=1, gpu=GPUOptions(frame_cache_mb=0))
        self.resources = []
        self.targets = []
        self.size = None
        try:
            self.ctx = self.native.ctx
            vertex = (ROOT / "raymarch.vert").read_text()
            fragment = (ROOT / "raymarch.frag").read_text()
            with self.ctx:
                self.program = self.ctx.program(vertex_shader=vertex, fragment_shader=fragment)
                self.resources.append(self.program)
                self.vbo = self.ctx.buffer(np.array([-1, -1, 3, -1, -1, 3], dtype="f4").tobytes())
                self.resources.append(self.vbo)
                self.vao = self.ctx.vertex_array(self.program, [(self.vbo, "2f", "in_position")])
                self.resources.append(self.vao)
            self.identity = {
                **self.native.identity,
                "raymarch_shader_hash": hashlib.sha256((vertex + fragment).encode()).hexdigest(),
                "geometry": "fragment-shader SDF ray marching; smooth unions, morphs, tunnel subtraction",
                "integration": "project-local GL viewport → public Image → ModernGL Bloom/composition",
            }
        except BaseException:
            self.close()
            raise

    def validate(self, scene):
        if scene.duration != DURATION:
            raise ValueError("Expected the fifteen-second ray-marched scene")
        self.native.validate(scene)

    def frame(self, scene, time, size):
        if not math.isfinite(time) or not 0 <= time <= DURATION:
            raise ValueError("source time must be in [0, 15]")
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
            self.ctx.enable_only(0)
            self.fbo.clear(0, 0, 0, 1)
            self.program["time"].value = time
            self.program["resolution"].value = size
            self.vao.render(moderngl.TRIANGLES)
            pixels = self.fbo.read(components=4, alignment=1)
            self.ctx.disable(moderngl.DEPTH_TEST)
        image = PILImage.frombytes("RGBA", size, pixels).transpose(PILImage.Transpose.FLIP_TOP_BOTTOM)
        sampled = Scene(scene.canvas)
        sampled.add(
            Image.from_source(
                image,
                width=1920,
                height=1080,
                position=(960, 540),
                effects=EffectStack(bloom=Bloom(radius=9, threshold=0.78, intensity=0.16)),
            )
        )
        sampled.wait_until(DURATION)
        return self.native.frame(sampled, time, size)

    def close(self):
        with self.native.ctx:
            for resource in reversed(self.resources + self.targets):
                resource.release()
        self.targets = []
        self.resources = []
        self.native.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--preview", action="store_true", help="One-second torus-to-tunnel morph sample at 9–10s")
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
        else "moderngl-raymarch.mp4"
    )
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite")
    if output.suffix.lower() != (".png" if args.frame is not None else ".mp4"):
        parser.error("output must use .png for a frame or .mp4 for video")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    settings = ExportSettings(backend="moderngl", antialias=1, quality=args.quality, fps=args.fps)
    source_range = args.range or ([9, 10] if args.preview else [0, DURATION])
    with RaymarchRenderer() as renderer:
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
