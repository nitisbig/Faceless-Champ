"""Owned GL resources, premultiplied targets and bounded multi-pass operations."""

import math
from collections import OrderedDict
from contextlib import contextmanager
from importlib.resources import files

from PIL import Image, ImageColor

from ..._portable import guard_size
from ...effects import _phase
from ...layout import Bounds
from ...motion import IDENTITY


def shader(name):
    return files(__package__).joinpath("shaders", name).read_text()


class Target:
    def __init__(self, texture, framebuffer=None, retained=False):
        self.texture, self.framebuffer, self.retained = texture, framebuffer, retained
        self.size = texture.size
        self.cost = math.prod(self.size) * texture.components * {"f1": 1, "f2": 2, "f4": 4}[texture.dtype]

    def release(self):
        if self.framebuffer is not None:
            self.framebuffer.release()
        self.texture.release()


class GLDevice:
    def __init__(self, ctx, gl, options):
        self.ctx, self.gl, self.options = ctx, gl, options
        self.programs, self.vaos = {}, {}
        self.pool, self.cache = [], OrderedDict()
        self.working_bytes = self.active_bytes = self.texture_bytes = 0
        self.particle_buffer = self.particle_vao = None
        self.particle_bytes = 0
        self.staging = bytearray()
        self.stats = {
            "uploads": 0,
            "upload_bytes": 0,
            "readbacks": 0,
            "draw_calls": 0,
            "texture_hits": 0,
            "peak_working_bytes": 0,
            "native_leaves": 0,
            "raster_leaves": 0,
        }
        try:
            with ctx:
                for name in ("copy", "effects", "background", "shape"):
                    p = ctx.program(vertex_shader=shader("quad.vert"), fragment_shader=shader(name + ".frag"))
                    self.programs[name] = p
                    self.vaos[name] = ctx.vertex_array(p, [])
                self.programs["particles"] = ctx.program(
                    vertex_shader=shader("particles.vert"), fragment_shader=shader("particles.frag")
                )
                for p in self.programs.values():
                    if "source" in p:
                        p["source"].value = 0
                    if "second" in p:
                        p["second"].value = 1
        except BaseException:
            self.close()
            raise

    @contextmanager
    def surface(self, size, color="#00000000", dtype="f2"):
        guard_size(size)
        with self.ctx:
            if max(size) > self.ctx.info["GL_MAX_TEXTURE_SIZE"]:
                raise ValueError("Target exceeds this GPU's maximum texture size")
        cost = math.prod(size) * 4 * ({"f1": 1, "f2": 2}[dtype])
        target = next((s for s in self.pool if s.size == size and s.texture.dtype == dtype), None)
        with self.ctx:
            if target is not None:
                self.pool.remove(target)
            else:
                while self.pool and self.working_bytes + self.particle_bytes + cost > self.options.working_mb * 1024**2:
                    old = self.pool.pop(0)
                    self.working_bytes -= old.cost
                    old.release()
                if self.working_bytes + self.particle_bytes + cost > self.options.working_mb * 1024**2:
                    raise ValueError("GPU targets exceed working_mb; reduce bounds, AA or scale")
                texture = self.ctx.texture(size, 4, dtype=dtype)
                texture.repeat_x = texture.repeat_y = False
                texture.filter = self.gl.LINEAR, self.gl.LINEAR
                try:
                    fbo = self.ctx.framebuffer([texture])
                except BaseException:
                    texture.release()
                    raise
                target = Target(texture, fbo)
                self.working_bytes += cost
        self.active_bytes += cost
        self.stats["peak_working_bytes"] = max(
            self.stats["peak_working_bytes"], self.working_bytes + self.particle_bytes
        )
        try:
            self.clear(target, color)
            yield target
        finally:
            self.active_bytes -= cost
            self.pool.append(target)

    def clear(self, target, color="#00000000"):
        r, g, b, a = (v / 255 for v in ImageColor.getcolor(color, "RGBA"))
        with self.ctx:
            target.framebuffer.clear(r * a, g * a, b * a, a)

    def cached(self, key):
        value = self.cache.get(key)
        if value is not None:
            self.cache.move_to_end(key)
            self.stats["texture_hits"] += 1
        return value

    def upload(self, image, key=None):
        guard_size(image.size)
        from ..._effects_cpu import numpy

        np = numpy()
        cost = image.width * image.height * 8
        if cost > self.options.working_mb * 1024**2:
            raise ValueError("Source texture exceeds working_mb")
        retained = key is not None and cost <= self.options.texture_cache_mb * 1024**2
        with self.ctx:
            if not retained:
                while self.pool and self.working_bytes + self.particle_bytes + cost > self.options.working_mb * 1024**2:
                    old = self.pool.pop(0)
                    self.working_bytes -= old.cost
                    old.release()
                if self.working_bytes + self.particle_bytes + cost > self.options.working_mb * 1024**2:
                    raise ValueError("Transient upload exceeds working_mb")
            pixels = np.asarray(image.convert("RGBA"), dtype="f4") / 255
            pixels[..., :3] *= pixels[..., 3:4]
            texture = self.ctx.texture(image.size, 4, pixels.astype("f2").tobytes(), dtype="f2")
            texture.repeat_x = texture.repeat_y = False
            texture.filter = self.gl.LINEAR, self.gl.LINEAR
            result = Target(texture)
            if retained:
                while self.cache and self.texture_bytes + cost > self.options.texture_cache_mb * 1024**2:
                    _, old = self.cache.popitem(last=False)
                    self.texture_bytes -= old.cost
                    old.release()
                result.retained = True
                self.cache[key] = result
                self.texture_bytes += cost
            else:
                self.working_bytes += cost
                self.active_bytes += cost
        self.stats["uploads"] += 1
        self.stats["upload_bytes"] += cost
        self.stats["raster_leaves"] += 1
        return result

    def release_upload(self, value):
        if not value.retained:
            with self.ctx:
                value.release()
            self.working_bytes -= value.cost
            self.active_bytes -= value.cost

    @staticmethod
    def uniforms(program, values):
        for name, value in values.items():
            if name in program:
                program[name].value = value

    def draw(self, target, name, box, world=IDENTITY, **values):
        with self.ctx:
            target.framebuffer.use()
            self.ctx.viewport = 0, 0, *target.size
            self.ctx.disable(self.gl.DEPTH_TEST | self.gl.CULL_FACE)
            self.ctx.enable(self.gl.BLEND)
            self.ctx.blend_func = self.gl.ONE, self.gl.ONE_MINUS_SRC_ALPHA
            p = self.programs[name]
            a, b, c, d, x, y = world
            self.uniforms(
                p,
                {
                    "target_size": target.size,
                    "rect": (box.left, box.top, box.width, box.height),
                    "transform": (a, b, 0, c, d, 0, x, y, 1),
                    **values,
                },
            )
            self.vaos[name].render(self.gl.TRIANGLE_STRIP, vertices=4)
            self.stats["draw_calls"] += 1

    def blit(self, target, source, box, world=IDENTITY, opacity=1):
        with self.ctx:
            source.texture.use(0)
            self.draw(target, "copy", box, world, opacity=opacity)

    def run(self, target, source, operation=0, second=None, **values):
        with self.ctx:
            source.texture.use(0)
            if second is not None:
                second.texture.use(1)
            # Pass replacement, not source-over: transparent output must erase old pixels.
            target.framebuffer.use()
            self.ctx.viewport = 0, 0, *target.size
            self.ctx.disable(self.gl.BLEND | self.gl.DEPTH_TEST | self.gl.CULL_FACE)
            p = self.programs["effects"]
            self.uniforms(
                p,
                {
                    "target_size": target.size,
                    "rect": (0, 0, *target.size),
                    "transform": (1, 0, 0, 0, 1, 0, 0, 0, 1),
                    "operation": operation,
                    **values,
                },
            )
            self.vaos["effects"].render(self.gl.TRIANGLE_STRIP, vertices=4)
            self.stats["draw_calls"] += 1

    def replace(self, target, operation, **values):
        with self.surface(target.size) as scratch:
            self.run(scratch, target, operation, **values)
            self.run(target, scratch)

    def blur(self, target, source, radius):
        from ..._effects_cpu import kernel

        if radius <= 0:
            self.run(target, source)
            return
        reduction = max(1, math.ceil(3 * radius / 64))
        size = max(1, math.ceil(source.size[0] / reduction)), max(1, math.ceil(source.size[1] / reduction))
        weights = kernel(radius / reduction)
        count = len(weights) // 2
        packed = [0.0] * 129
        packed[64 - count : 65 + count] = [float(w) for w in weights]
        if reduction == 1 and target.size == source.size:
            with self.surface(size) as scratch:
                self.run(scratch, source, 3, direction=(1 / size[0], 0), count=count, weights=tuple(packed))
                self.run(target, scratch, 3, direction=(0, 1 / size[1]), count=count, weights=tuple(packed))
        else:
            with self.surface(size) as first, self.surface(size) as second:
                self.run(first, source)
                self.run(second, first, 3, direction=(1 / size[0], 0), count=count, weights=tuple(packed))
                self.run(first, second, 3, direction=(0, 1 / size[1]), count=count, weights=tuple(packed))
                self.run(target, first)

    def content(self, target, stack, scale, time, content_box=None):
        if stack is None or not any((stack.blur, stack.distortion, stack.chromatic, stack.light_sweep)):
            return
        self.replace(target, 1)
        w, _ = target.size
        logical_box = content_box or (0, 0, *target.size)
        if (e := stack.light_sweep) is not None:
            self.replace(
                target, 6, params=(e.intensity, _phase(time, e.speed, 1) % 1, e.width, 0), logical_box=logical_box
            )
        if (e := stack.distortion) is not None:
            self.replace(
                target,
                4,
                params=(e.amplitude * scale / w, e.frequency, _phase(time, e.speed), 0),
                logical_box=logical_box,
            )
        if (e := stack.chromatic) is not None:
            self.replace(target, 5, params=(e.offset * scale / w, 0, 0, 0))
        if (e := stack.blur) is not None and e.radius:
            with self.surface(target.size) as scratch:
                self.blur(scratch, target, e.radius * scale)
                self.run(target, scratch)
        self.replace(target, 2)

    def mask(self, target, image):
        mask = self.upload(image)
        try:
            self.replace(target, 11, second=mask)
        finally:
            self.release_upload(mask)

    def halos(self, target, stack, scale):
        if stack is None or not any((stack.glow, stack.bloom)):
            return
        with self.surface(target.size) as base:
            self.run(base, target, 1)
            self.run(target, base)
            if (e := stack.glow) is not None and e.intensity:
                with self.surface(target.size) as halo, self.surface(target.size) as cast:
                    self.blur(cast, base, e.radius * scale)
                    self.run(
                        halo,
                        cast,
                        7,
                        tint=tuple(v / 255 for v in ImageColor.getcolor(e.color, "RGBA")),
                        params=(e.intensity, 0, 0, 0),
                    )
                    self.replace(target, 9, second=halo)
            if (e := stack.bloom) is not None and e.intensity:
                with self.surface(target.size) as bright, self.surface(target.size) as accumulated:
                    self.run(bright, base, 8, params=(e.threshold, 0, 0, 0))
                    for level in (1, 2, 4):
                        size = max(1, math.ceil(target.size[0] / level)), max(1, math.ceil(target.size[1] / level))
                        with self.surface(size) as low, self.surface(size) as light:
                            self.run(low, bright)
                            self.blur(light, low, e.radius * scale / level)
                            self.replace(accumulated, 18, second=light, params=(1 / 3, 0, 0, 0))
                    self.replace(target, 10, second=accumulated, params=(e.intensity, 0, 0, 0))
            self.replace(target, 2)

    def shadow(self, target, shadow, scale, include_content=True):
        if shadow is None:
            return
        with self.surface(target.size) as blurred, self.surface(target.size) as cast:
            self.blur(blurred, target, shadow.blur * scale)
            self.run(
                cast,
                blurred,
                12,
                tint=tuple(v / 255 for v in ImageColor.getcolor(shadow.color, "RGBA")),
                params=(shadow.offset[0] * scale / target.size[0], shadow.offset[1] * scale / target.size[1], 0, 0),
            )
            if include_content:
                self.replace(target, 9, second=cast)
            else:
                self.run(target, cast)

    def mix(self, target, first, second, progress, transition):
        from ...transitions import LuminanceWipe, ZoomBlurTransition

        kind = (
            0
            if transition is None
            else 3
            if isinstance(transition, ZoomBlurTransition)
            else 2
            if isinstance(transition, LuminanceWipe)
            else 1
        )
        parameter = 0 if transition is None else transition.strength if kind == 3 else transition.softness
        self.run(
            target,
            first,
            15 if transition is None else 16,
            second=second,
            progress=progress,
            transition_kind=kind,
            params=(parameter, 0, 0, 0),
        )

    def component(self, target, c, state, box, world, opacity, age):
        from ...components import Circle, Ellipse, Rectangle
        from ...gradients import LinearGradient, RadialGradient
        from ...motion import rgba
        from ...procedural import ParticleField, ProceduralBackground, particle_data
        from ...surfaces import Surface

        if isinstance(c, ParticleField):
            records = particle_data(c, age).tobytes()
            with self.ctx:
                if self.particle_bytes < len(records):
                    while self.pool and self.working_bytes + len(records) > self.options.working_mb * 1024**2:
                        old = self.pool.pop(0)
                        self.working_bytes -= old.cost
                        old.release()
                    if self.working_bytes + len(records) > self.options.working_mb * 1024**2:
                        raise ValueError("Particle buffer exceeds working_mb")
                    if self.particle_vao is not None:
                        self.particle_vao.release()
                        self.particle_buffer.release()
                    self.particle_buffer = self.ctx.buffer(reserve=len(records))
                    self.particle_bytes = len(records)
                    self.particle_vao = self.ctx.vertex_array(
                        self.programs["particles"], [(self.particle_buffer, "3f /i", "instance")]
                    )
                self.particle_buffer.write(records)
                target.framebuffer.use()
                self.ctx.viewport = 0, 0, *target.size
                self.ctx.disable(self.gl.DEPTH_TEST | self.gl.CULL_FACE)
                self.ctx.enable(self.gl.BLEND)
                self.ctx.blend_func = self.gl.ONE, self.gl.ONE_MINUS_SRC_ALPHA
                a, b, cc, d, x, y = world
                self.uniforms(
                    self.programs["particles"],
                    {
                        "target_size": target.size,
                        "transform": (a, b, 0, cc, d, 0, x, y, 1),
                        "origin": (c.width / 2, c.height / 2),
                        "radius": c.radius,
                        "opacity": opacity,
                        "color": tuple(v / 255 for v in ImageColor.getcolor(c.color, "RGBA")),
                    },
                )
                self.particle_vao.render(self.gl.TRIANGLE_STRIP, vertices=4, instances=c.count)
                self.stats["draw_calls"] += 1
                self.stats["upload_bytes"] += len(records)
            return True
        if isinstance(c, ProceduralBackground):
            self.draw(
                target,
                "background",
                Bounds(-c.width / 2, -c.height / 2, c.width / 2, c.height / 2),
                world,
                time=c.frame_key(age) + (c.seed % 65536) / 65536,
                kind=0 if c.kind == "aurora" else 1,
                color=tuple(v / 255 for v in ImageColor.getcolor(c.color, "RGBA")),
                opacity=opacity,
            )
            return True
        if isinstance(c, Surface):
            if c.surface_shadow or c.pattern:
                return False
            w, h, fill, radius = c.width, c.height, c.fill, c.radius
            stroke, sw = (0, 0, 0, 0), 0
        elif isinstance(c, (Rectangle, Circle, Ellipse)) and state["draw"] >= 1:
            w, h, fill, radius = state["width"], state["height"], state["fill"], state.get("corner_radius", 0)
            stroke, sw = state["stroke"], state["stroke_width"]
        else:
            return False

        def premul(value):
            r, g, b, a = (v / 255 for v in rgba(value))
            return r * a, g * a, b * a, a

        values = {
            "extent": (w, h),
            "radius": min(radius, w / 2, h / 2),
            "ellipse": int(isinstance(c, (Circle, Ellipse))),
            "stroke_color": premul(stroke),
            "stroke_width": sw,
            "opacity": opacity,
            "paint_kind": 0,
            "fill_color": (0, 0, 0, 0),
        }
        if isinstance(fill, (LinearGradient, RadialGradient)):
            colors = [premul(stop._rgba) for stop in fill.stops]
            offsets = [stop.offset for stop in fill.stops]
            values.update(
                stop_count=len(colors),
                colors=tuple(colors + [(0, 0, 0, 0)] * (64 - len(colors))),
                stops=tuple(offsets + [1.0] * (64 - len(offsets))),
            )
            if isinstance(fill, LinearGradient):
                angle = math.radians(fill.angle)
                values.update(paint_kind=1, gradient=(math.cos(angle), math.sin(angle), 0, 0))
            else:
                values.update(paint_kind=2, gradient=(*fill.center, fill.radius, 0))
        else:
            values["fill_color"] = premul(fill)
        self.draw(target, "shape", box, world, **values)
        self.stats["native_leaves"] += 1
        return True

    def finish(self, target, size):
        with self.surface(size, dtype="f1") as out:
            self.run(out, target, 17, factor=target.size[0] / size[0], output_size=size)
            cost = math.prod(size) * 4
            if len(self.staging) != cost:
                self.staging = bytearray(cost)
            with self.ctx:
                out.framebuffer.read_into(self.staging, components=4, alignment=1)
            self.stats["readbacks"] += 1
            return Image.frombytes("RGBA", size, bytes(self.staging))

    def close(self):
        with self.ctx:
            for target in [*self.pool, *self.cache.values()]:
                target.release()
            self.pool.clear()
            self.cache.clear()
            for value in (self.particle_vao, self.particle_buffer, *self.vaos.values(), *self.programs.values()):
                if value is not None:
                    value.release()
            self.vaos.clear()
            self.programs.clear()
        self.particle_vao = self.particle_buffer = None
        self.working_bytes = self.active_bytes = self.texture_bytes = self.particle_bytes = 0
        self.staging.clear()
