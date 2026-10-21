"""Complex iteration and linked Mandelbrot/Julia planes; native Cairo, no TeX."""

import numpy as np
from manim import Circle, Dot, ImageMobject, Line, Rectangle, Scene, Text, ValueTracker, VGroup, config, linear
from manim.camera.camera import Camera
from PIL import Image

DURATION = 15.0
CYAN, GOLD, PINK, MUTED = "#55DDEB", "#FFD166", "#F783AC", "#465766"
LEFT, RIGHT = np.array([-3.35, -0.15, 0]), np.array([3.35, -0.15, 0])
SIDE = 5.5
M_BOUNDS = (-2.1, 0.8, -1.45, 1.45)
J_BOUNDS = (-1.6, 1.6, -1.6, 1.6)


def smooth(value):
    u = np.clip(value, 0, 1)
    return float(u * u * (3 - 2 * u))


def grid(size, bounds):
    left, right, bottom, top = bounds
    return np.linspace(left, right, size)[None, :] + 1j * np.linspace(top, bottom, size)[:, None]


def escape_field(initial, parameter, iterations=144):
    """Smooth escape times, updating only live points to avoid overflow."""
    z, c = np.broadcast_arrays(np.asarray(initial, complex), np.asarray(parameter, complex))
    z = z.copy()
    live = np.ones(z.shape, dtype=bool)
    values = np.zeros(z.shape)
    for n in range(iterations):
        z[live] = z[live] ** 2 + c[live]
        escaped = live & (np.abs(z) > 4)
        values[escaped] = n + 1 - np.log2(np.log2(np.abs(z[escaped])))
        live[escaped] = False
        if not live.any():
            break
    return values, live


def fractal_pixels(initial, parameter, iterations=144):
    values, interior = escape_field(initial, parameter, iterations)
    # Smooth bands hug a black interior; distant exterior fades into the canvas.
    phase = values * 0.085
    palette = np.array([[8, 12, 25], [26, 95, 160], [85, 221, 235], [255, 209, 102], [247, 131, 172]])
    u = np.mod(phase, len(palette))
    index = u.astype(int)
    rgb = palette[index] * (1 - (u % 1)[..., None]) + palette[(index + 1) % len(palette)] * (u % 1)[..., None]
    rgb *= (1 - np.exp(-np.maximum(values, 0) / 4))[..., None]
    rgb[interior] = 0
    return np.dstack((rgb.astype(np.uint8), np.full(values.shape, 255, dtype=np.uint8)))


def orbit(c, steps=16):
    result = [0j]
    for _ in range(steps):
        result.append(result[-1] ** 2 + c)
        if abs(result[-1]) > 2:
            break
    return np.array(result)


def parameter_at(time):
    if time < 4:
        return -0.5 + 0.5j
    if time < 8:
        return 0.7 + 0.2j
    stops = (-0.8 + 0.156j, -0.4 + 0.6j, 0.285 + 0.01j)
    phase = min((time - 8) / 3.5, 2)
    index = min(int(phase), 1)
    return stops[index] + (stops[index + 1] - stops[index]) * smooth(phase - index)


def label(value, point, color=MUTED, size=22):
    return Text(value, font="DejaVu Sans", font_size=size, color=color).move_to(point)


def map_parameter(value):
    return LEFT + [SIDE * (value.real + 0.65) / 2.9, SIDE * value.imag / 2.9, 0]


def map_orbit(value):
    return RIGHT + [1.16 * value.real, 1.16 * value.imag, 0]


class FractalCamera(Camera):
    """Axis-aligned raster support avoiding Manim 0.22's float RGBA canvas."""

    def display_image_mobject(self, image_mobject, pixel_array):
        corners = self.points_to_subpixel_coords(image_mobject, image_mobject.points)
        left, top = np.floor(corners.min(axis=0)).astype(int)
        right, bottom = np.ceil(corners.max(axis=0)).astype(int)
        if right <= left or bottom <= top:
            return
        tile = Image.fromarray(image_mobject.get_pixel_array()).resize(
            (right - left, bottom - top), Image.Resampling.BILINEAR
        )
        layer = Image.new("RGBA", (self.pixel_width, self.pixel_height))
        layer.paste(tile, (left, top))
        self.overlay_PIL_image(pixel_array, layer)


class ComplexFractals(Scene):
    def __init__(self, **kwargs):
        super().__init__(camera_class=FractalCamera, **kwargs)

    def construct(self):
        config.background_color = "#000000"
        size = min(720, max(240, int(config.pixel_height * 0.72)))
        m_grid, j_grid = grid(size, M_BOUNDS), grid(size, J_BOUNDS)
        mandelbrot = ImageMobject(fractal_pixels(0j, m_grid)).set_height(SIDE).move_to(LEFT)
        julia = ImageMobject(fractal_pixels(j_grid, parameter_at(8))).set_height(SIDE).move_to(RIGHT)
        julia.set_opacity(0)
        julia.add_updater(lambda mob: None)  # Keep changing pixels out of Cairo's static-frame cache.
        self.add(mandelbrot, julia)
        self.add(label("zₙ₊₁ = zₙ² + c", [0, 3.3, 0], "#E4EDF4", 32))
        for center in (LEFT, RIGHT):
            self.add(Rectangle(width=SIDE, height=SIDE, color=MUTED, stroke_width=1).move_to(center))
        self.add(label("c ∈ ℂ", [-3.35, -3.28, 0], CYAN))
        clock = ValueTracker(0)
        dynamic = VGroup()
        image_state = [None]

        def update(mob):
            time = clock.get_value()
            c = parameter_at(time)
            items = VGroup()
            # Mandelbrot's real and imaginary axes remain a subtle coordinate reference.
            origin = map_parameter(0j)
            items.add(
                Line(
                    [LEFT[0] - SIDE / 2, origin[1], 0],
                    [LEFT[0] + SIDE / 2, origin[1], 0],
                    color=MUTED,
                    stroke_width=0.6,
                    stroke_opacity=0.6,
                )
            )
            items.add(
                Line(
                    [origin[0], LEFT[1] - SIDE / 2, 0],
                    [origin[0], LEFT[1] + SIDE / 2, 0],
                    color=MUTED,
                    stroke_width=0.6,
                    stroke_opacity=0.6,
                )
            )
            marker = map_parameter(c)
            items.add(
                Circle(radius=0.13, color=GOLD, stroke_width=2).move_to(marker),
                Dot(marker, radius=0.035, color="WHITE"),
            )
            items.add(label(f"c = {c.real:+.3f} {c.imag:+.3f}i", [0, 2.83, 0], GOLD, 19))
            if time < 8:
                for direction in ([SIDE / 2, 0, 0], [0, SIDE / 2, 0]):
                    vector = np.array(direction)
                    items.add(Line(RIGHT - vector, RIGHT + vector, color=MUTED, stroke_width=1))
                items.add(Circle(radius=2 * 1.16, color=MUTED, stroke_width=1, stroke_opacity=0.55).move_to(RIGHT))
                items.add(
                    label("Re", RIGHT + [2.47, -0.22, 0], size=16), label("Im", RIGHT + [-0.24, 2.47, 0], size=16)
                )
                values = orbit(c)
                progress = np.clip((time % 4) / 3.4, 0, 1) * (len(values) - 1)
                step = min(int(progress), len(values) - 2)
                fraction = smooth(progress - step)
                # Each step first maps z to z² (gold), then translates by c (cyan).
                z, square = values[step], values[step] ** 2
                mapped = (
                    z + (square - z) * smooth(fraction * 2) if fraction < 0.5 else square + c * smooth(fraction * 2 - 1)
                )
                for index in range(step):
                    a, b = map_orbit(values[index]), map_orbit(values[index + 1])
                    items.add(
                        Line(a, b, color=CYAN, stroke_width=1.5, stroke_opacity=0.55), Dot(b, color=CYAN, radius=0.035)
                    )
                start, squared = map_orbit(z), map_orbit(square)
                if fraction < 0.5:
                    items.add(Line(start, map_orbit(mapped), color=GOLD, stroke_width=2.5))
                else:
                    items.add(
                        Line(start, squared, color=GOLD, stroke_width=2),
                        Line(squared, map_orbit(mapped), color=CYAN, stroke_width=2.5),
                    )
                items.add(Dot(map_orbit(mapped), color=PINK if abs(mapped) > 2 else "WHITE", radius=0.07))
                items.add(
                    label("z₀ = 0", [3.35, -3.28, 0], CYAN),
                    label("z → z²", [2.25, -2.6, 0], GOLD, 19),
                    label("+ c", [4.6, -2.6, 0], CYAN, 19),
                )
            else:
                # Fixed z₀ window: only c changes, directly linked to the left marker.
                key = round(time, 6)
                if image_state[0] != key:
                    julia.pixel_array = fractal_pixels(j_grid, c)
                    image_state[0] = key
                julia.set_opacity(smooth((time - 8) / 0.45))
                items.add(label("z₀ ∈ ℂ", [3.35, -3.28, 0], CYAN))
                items.add(
                    Line(marker, [RIGHT[0] - SIDE / 2, marker[1], 0], color=GOLD, stroke_width=1, stroke_opacity=0.45)
                )
            mob.remove(*mob.submobjects)
            mob.add(*items.submobjects)

        dynamic.add_updater(update)
        self.add(dynamic)
        self.play(clock.animate.set_value(DURATION), run_time=DURATION, rate_func=linear)
        dynamic.clear_updaters()
