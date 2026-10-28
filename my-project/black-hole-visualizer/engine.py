"""GPU simulator: a camera rig plus a ModernGL geodesic tracer exposed as a Faceless Champ source."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import physics

SHADER_DIR = Path(__file__).resolve().parent / "shaders"
VERTEX = """
#version 330 core
in vec2 in_position;
out vec2 v_uv;
void main() {
    v_uv = in_position * 0.5 + 0.5;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""
SHADER_HASH = hashlib.sha256((VERTEX + (SHADER_DIR / "blackhole.frag").read_text()).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- camera


@dataclass(frozen=True)
class Shot:
    """Camera keyframe. Angles in degrees; inclination is measured from the disk axis."""

    t: float
    r: float
    incl: float
    az: float
    fov: float = 34.0
    shift: float = 0.0  # horizontal lens shift in NDC (positive moves the hole left)


@dataclass(frozen=True)
class CameraState:
    position: np.ndarray
    basis: np.ndarray  # columns right, up, forward
    fov: float
    shift: float
    r: float


class CameraRig:
    """Catmull–Rom spline through keyframes: continuous velocity, no stops between shots."""

    FIELDS = ("r", "incl", "az", "fov", "shift")

    def __init__(self, shots: list[Shot]):
        self.shots = sorted(shots, key=lambda s: s.t)

    def values(self, t: float) -> dict[str, float]:
        s = self.shots
        t = min(max(t, s[0].t), s[-1].t)
        i = max(0, min(len(s) - 2, next((k for k in range(len(s) - 1) if t <= s[k + 1].t), len(s) - 2)))
        p0, p1, p2, p3 = s[max(i - 1, 0)], s[i], s[i + 1], s[min(i + 2, len(s) - 1)]
        u = (t - p1.t) / (p2.t - p1.t)
        u = u * u * (3 - 2 * u) * 0.35 + u * 0.65  # soften departures without full stops
        out = {}
        for name in self.FIELDS:
            a, b, c, d = (getattr(p, name) for p in (p0, p1, p2, p3))
            # Tangents scaled by neighbouring interval lengths (non-uniform keyframe spacing).
            m1 = (c - a) / max(p2.t - p0.t, 1e-6) * (p2.t - p1.t)
            m2 = (d - b) / max(p3.t - p1.t, 1e-6) * (p2.t - p1.t)
            u2, u3 = u * u, u * u * u
            out[name] = (2 * u3 - 3 * u2 + 1) * b + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * c + (u3 - u2) * m2
        return out

    def state(self, t: float) -> CameraState:
        v = self.values(t)
        inc, az = math.radians(v["incl"]), math.radians(v["az"])
        pos = v["r"] * np.array([math.sin(inc) * math.cos(az), math.sin(inc) * math.sin(az), math.cos(inc)])
        forward = -pos / np.linalg.norm(pos)
        right = np.cross(forward, [0.0, 0.0, 1.0])
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        return CameraState(pos, np.stack([right, up, forward], axis=1), v["fov"], v["shift"], v["r"])

    def project(self, point, t: float, size: tuple[int, int]) -> tuple[float, float]:
        """Straight-line pinhole projection to pixels (valid where lensing is mild, e.g. the near disk)."""
        cam = self.state(t)
        local = cam.basis.T @ (np.asarray(point, float) - cam.position)
        tan_half = math.tan(math.radians(cam.fov) / 2)
        w, h = size
        ndc_x = local[0] / local[2] / tan_half / (w / h) - cam.shift
        ndc_y = local[1] / local[2] / tan_half
        return ((ndc_x + 1) / 2 * w, (1 - ndc_y) / 2 * h)

    def shadow_edge(self, t: float, size: tuple[int, int]) -> float:
        """Apparent shadow radius in pixels at time t."""
        cam = self.state(t)
        return math.tan(physics.shadow_angular_radius(cam.r)) / math.tan(math.radians(cam.fov) / 2) * size[1] / 2


# --------------------------------------------------------------------------- tracer


class BlackHoleEngine:
    """Owns a headless GL context; render(t, size) returns an RGB uint8 frame."""

    def __init__(self, rig: CameraRig, *, samples: int = 1, time_scale: float = 22.0, t_peak_kelvin: float = 4300.0):
        import moderngl

        self.moderngl = moderngl
        self.rig = rig
        self.time_scale = time_scale
        self.ctx = moderngl.create_standalone_context(require=330, backend="egl")
        self.prog = self.ctx.program(vertex_shader=VERTEX, fragment_shader=(SHADER_DIR / "blackhole.frag").read_text())
        self.vbo = self.ctx.buffer(np.array([-1, -1, 3, -1, -1, 3], dtype="f4").tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f", "in_position")])
        lut = physics.blackbody_lut(256)
        self.lut = self.ctx.texture((256, 1), 3, lut.tobytes(), dtype="f4")
        self.lut.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.lut.repeat_x = False
        self.lut.use(0)
        self._set(
            blackbody=0,
            samples=samples,
            disk_in=physics.R_ISCO,
            disk_out=21.0,
            t4_peak=physics._T4_PEAK,
            t_peak_kelvin=t_peak_kelvin,
            lut_range=(math.log(physics.LUT_T_MIN), math.log(physics.LUT_T_MAX)),
            exposure=0.9,
        )
        self.fbo = None
        self.size = None
        self.renderer = self.ctx.info["GL_RENDERER"]

    def _set(self, **uniforms):
        for name, value in uniforms.items():
            if name in self.prog:
                self.prog[name].value = value

    def render(self, t: float, size: tuple[int, int]) -> np.ndarray:
        with self.ctx:
            if self.size != size:
                if self.fbo is not None:
                    self.fbo.release()
                self.fbo = self.ctx.simple_framebuffer(size, components=4)
                self.size = size
            cam = self.rig.state(t)
            self.fbo.use()
            self.lut.use(0)
            self._set(
                resolution=size,
                cam_pos=tuple(cam.position),
                cam_basis=tuple(cam.basis.T.flatten()),  # GLSL mat3 is column-major
                tan_half_fov=math.tan(math.radians(cam.fov) / 2),
                lens_shift=(cam.shift, 0.0),
                sim_time=t * self.time_scale,
            )
            self.vao.render(self.moderngl.TRIANGLES)
            raw = self.fbo.read(components=3, alignment=1)
        return np.frombuffer(raw, np.uint8).reshape(size[1], size[0], 3)[::-1].copy()

    def close(self):
        for obj in (self.fbo, self.vao, self.vbo, self.lut, self.prog):
            if obj is not None:
                obj.release()
        self.ctx.release()


def source(rig: CameraRig, duration: float, size=(1920, 1080), samples: int = 1):
    """Faceless Champ FunctionSource; one engine per render session."""
    from faceless_champ import FunctionSource

    def frame(t, px_size, engine):
        return engine.render(t, px_size)

    return FunctionSource(
        frame,
        size=size,
        duration=duration,
        setup=lambda _size: BlackHoleEngine(rig, samples=samples),
        key=f"blackhole:{SHADER_HASH}:{samples}:{hash(tuple(rig.shots))}",
    )
