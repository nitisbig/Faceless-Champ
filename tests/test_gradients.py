"""Independent numeric, validation and raster checks for immutable gradient paints."""

import math
import random
from dataclasses import FrozenInstanceError
from io import BytesIO

import pytest
from PIL import Image

from faceless_champ import Bounds, GradientStop, LinearGradient, RadialGradient, gradient_surface
from faceless_champ.gradients import _parameter, _sample


def stops(*colors):
    return tuple(GradientStop(i / (len(colors) - 1), color) for i, color in enumerate(colors))


def pixels(paint, width=31, height=23):
    component = gradient_surface(Bounds(0, 0, width, height), fill=paint)
    with Image.open(BytesIO(component.source_bytes)) as source:
        return source.convert("RGBA")


def test_immutable_normalized_and_hashable_descriptions():
    values = [GradientStop(0, "red"), GradientStop(1, "#0000FF00")]
    center = [0.2, 0.7]
    linear = LinearGradient(values, angle=-270)
    radial = RadialGradient(values, center=center)
    values.clear()
    center[0] = 1
    assert linear.angle == 90 and len(linear.stops) == 2
    assert radial.center == (0.2, 0.7)
    assert linear.stops[0].color == "#FF0000FF"
    assert linear.stops[1].color == "#00000000"
    assert hash(linear) == hash(LinearGradient(stops("red", "#00000000"), 90))
    for obj, key, value in ((linear, "angle", 0), (radial, "radius", 2), (linear.stops[0], "offset", 0.5)):
        with pytest.raises(FrozenInstanceError):
            setattr(obj, key, value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -0.1, 1.1, True, "bad", 10**1000])
def test_invalid_stop_offset(value):
    with pytest.raises(ValueError):
        GradientStop(value, "red")


@pytest.mark.parametrize("color", ["", "#12", "not-a-color", "#GG0000"])
def test_invalid_color(color):
    with pytest.raises(ValueError, match="color"):
        GradientStop(0, color)


def test_invalid_stop_collections_are_bounded_and_not_sorted():
    from itertools import repeat

    for values in (
        (),
        (GradientStop(0, "red"),),
        tuple(GradientStop(i / 64, "red") for i in range(65)),
        stops("red", "blue")[::-1],
        (GradientStop(0.5, "red"), GradientStop(0.5, "blue")),
        repeat(GradientStop(0, "red")),
    ):
        with pytest.raises(ValueError):
            LinearGradient(values)
    with pytest.raises(TypeError):
        LinearGradient(("red", "blue"))
    with pytest.raises(TypeError):
        GradientStop(0, (255, 0, 0, 255))


@pytest.mark.parametrize("kwargs", [{"angle": float("nan")}, {"angle": float("inf")}])
def test_invalid_linear(kwargs):
    with pytest.raises(ValueError):
        LinearGradient(stops("red", "blue"), **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"center": (0,)},
        {"center": (0, 0, 0)},
        {"center": None},
        {"center": (-0.1, 0.5)},
        {"center": (0.5, 1.1)},
        {"center": (float("nan"), 0.5)},
        {"center": (float("inf"), 0.5)},
        {"radius": 0},
        {"radius": -1},
        {"radius": 1e-8},
        {"radius": 17},
        {"radius": float("nan")},
        {"radius": float("inf")},
    ],
)
def test_invalid_radial(kwargs):
    with pytest.raises(ValueError):
        RadialGradient(stops("red", "blue"), **kwargs)


def test_scalar_exact_stops_extension_and_premultiplied_alpha():
    gradient = LinearGradient(
        (GradientStop(0.2, "#FF0000"), GradientStop(0.5, "#00FF0080"), GradientStop(0.8, "#0000FF00"))
    )
    assert _sample(gradient, 0) == _sample(gradient, 0.2) == (255, 0, 0, 255)
    assert _sample(gradient, 0.5) == (0, 255, 0, 128)
    assert _sample(gradient, 0.8) == _sample(gradient, 1) == (0, 0, 0, 0)
    # Opaque red to invisible blue stays red as coverage fades, rather than turning purple.
    fade = LinearGradient(stops("red", "#0000FF00"))
    assert _sample(fade, 0.5) == (255, 0, 0, 128)
    # Encoded-sRGB midpoint, explicitly not linear-light 188.
    assert _sample(LinearGradient(stops("black", "white")), 0.5) == (128, 128, 128, 255)


@pytest.mark.parametrize(
    "angle,start,end",
    [
        (0, (0, 10), (61, 10)),
        (90, (10, 0), (10, 45)),
        (180, (61, 10), (0, 10)),
        (270, (10, 45), (10, 0)),
    ],
)
def test_raster_cardinal_directions_and_exact_endpoints(angle, start, end):
    with pixels(LinearGradient(stops("red", "blue"), angle)) as image:
        assert image.getpixel(start) == (255, 0, 0, 255)
        assert image.getpixel(end) == (0, 0, 255, 255)


def test_radial_is_circular_in_design_pixels_and_offcenter():
    gradient = RadialGradient(stops("white", "black"), center=(0.25, 0.5), radius=0.5)
    assert _parameter(gradient, 0.25, 0.5, 200, 100) == 0
    assert _parameter(gradient, 0.5, 0.5, 200, 100) == 1
    assert _parameter(gradient, 0.25, 1, 200, 100) == 1
    with pixels(gradient, 100, 50) as image:
        assert image.getpixel((0, 0)) == (0, 0, 0, 255)
        assert min(image.getpixel((50, 50))[:3]) > 245


@pytest.mark.parametrize(
    "width,height,center,sample",
    [
        (1, 1000, (0, 0.5002506750625313), (0, 1000)),
        (1000, 1, (0.5002506750625313, 0), (1000, 0)),
    ],
)
def test_thin_radial_surface_preserves_subpixel_distance_precision(width, height, center, sample):
    gradient = RadialGradient(stops("white", "black"), center=center, radius=0.0011)
    with pixels(gradient, width, height) as image:
        x, y = sample[0] / (image.width - 1), sample[1] / (image.height - 1)
        distance = math.hypot((x - center[0]) * width, (y - center[1]) * height)
        expected = math.floor(255 * (1 - distance / (gradient.radius * min(width, height))) + 0.5)
        assert expected == 128
        assert image.getpixel(sample) == (expected, expected, expected, 255)


@pytest.mark.parametrize(
    "paint",
    [
        LinearGradient(stops("#FF000000", "#00FF0080", "#2020FFFF"), 125),
        RadialGradient(stops("#FFEEDD", "#37A2A080", "#2200FF00"), center=(0.17, 0.82), radius=0.8),
        LinearGradient(
            (GradientStop(0, "red"), GradientStop(0.50000000001, "blue"), GradientStop(0.50000000002, "white")), 47
        ),
        RadialGradient(stops("white", "#00000000"), radius=1e-6),
    ],
)
def test_tiled_pixels_match_independent_double_precision_reference(paint):
    rng = random.Random(2016)
    with pixels(paint, 37, 79) as image:
        for x, y in [(0, 0), (73, 157), (0, 157), (73, 0), (36, 78)] + [
            (rng.randrange(74), rng.randrange(158)) for _ in range(100)
        ]:
            nx, ny = x / 73, y / 157
            if isinstance(paint, LinearGradient):
                dx, dy = math.cos(math.radians(paint.angle)) * 37, math.sin(math.radians(paint.angle)) * 79
                t = (nx * dx + ny * dy - min(0, dx) - min(0, dy)) / (abs(dx) + abs(dy))
            else:
                t = math.hypot((nx - paint.center[0]) * 37, (ny - paint.center[1]) * 79) / (paint.radius * 37)
            t = min(1, max(0, t))
            # Independent weighted-alpha reference instead of calling production color interpolation.
            left, right = paint.stops[0], paint.stops[-1]
            if t <= left.offset:
                expected = left._rgba
            elif t >= right.offset:
                expected = right._rgba
            else:
                for a, b in zip(paint.stops, paint.stops[1:]):
                    if a.offset <= t <= b.offset:
                        u = (t - a.offset) / (b.offset - a.offset)
                        alpha = (1 - u) * a._rgba[3] + u * b._rgba[3]
                        expected = (
                            (0, 0, 0, 0)
                            if math.floor(alpha + 0.5) == 0
                            else (
                                *(
                                    math.floor(
                                        ((1 - u) * a._rgba[i] * a._rgba[3] + u * b._rgba[i] * b._rgba[3]) / alpha + 0.5
                                    )
                                    for i in range(3)
                                ),
                                math.floor(alpha + 0.5),
                            )
                        )
                        break
            actual = image.getpixel((x, y))
            assert max(abs(a - b) for a, b in zip(actual, expected)) <= 1, (x, y, actual, expected)


def test_allocations_fail_before_any_pillow_allocation(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Pillow allocation happened before validation")

    gradient = LinearGradient(stops("red", "blue"))
    monkeypatch.setattr("faceless_champ._surface_raster.Image.new", fail)
    for bounds in (Bounds(0, 0, 0, 10), Bounds(0, 0, 5000, 10), Bounds(0, 0, 3000, 3000), Bounds(-1e308, 0, 1e308, 10)):
        with pytest.raises(ValueError):
            gradient_surface(bounds, fill=gradient)


def test_unsupported_fills_and_reserved_geometry():
    with pytest.raises(TypeError, match="fill"):
        gradient_surface(Bounds(0, 0, 20, 20), fill="red")
    with pytest.raises(TypeError, match="reserve geometry"):
        gradient_surface(Bounds(0, 0, 20, 20), fill=LinearGradient(stops("red", "blue")), trim=True)


@pytest.mark.parametrize("option", ["radius", "shadow"])
def test_rectangular_backdrop_does_not_accept_card_style_overrides(option):
    with pytest.raises(TypeError, match="multiple values"):
        gradient_surface(Bounds(0, 0, 20, 20), fill=LinearGradient(stops("red", "blue")), **{option: None})


def test_many_stop_native_fields_stay_within_one_channel_level():
    from faceless_champ._surface_raster import _paint

    rng = random.Random(71)
    for index in range(80):
        count = rng.choice((2, 3, 8, 64))
        values = tuple(
            GradientStop(j / (count - 1), "#" + "".join(f"{rng.randrange(256):02x}" for _ in range(4)))
            for j in range(count)
        )
        gradient = (
            LinearGradient(values, angle=rng.uniform(-360, 360))
            if index % 2
            else RadialGradient(values, center=(rng.random(), rng.random()), radius=rng.uniform(0.05, 3))
        )
        with _paint(gradient, 40, 30, (80, 60)) as image:
            for _ in range(200):
                x, y = rng.randrange(80), rng.randrange(60)
                expected = _sample(gradient, _parameter(gradient, x / 79, y / 59, 40, 30))
                assert max(abs(a - b) for a, b in zip(expected, image.getpixel((x, y)))) <= 1
