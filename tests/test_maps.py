import builtins
import hashlib
import json

import pytest
from PIL import Image

from faceless_champ import Canvas, EarthMap, OutlineMap, PillowRenderer, SatelliteMap, Scene, linear, maps


def test_lookup_and_assets():
    assert len(maps.supported_countries()) == 177
    assert OutlineMap("NP").country == OutlineMap("npl").country == "Nepal"
    for name in maps.OCEANS:
        assert SatelliteMap().zoom_to(name).zoom > 0
    assert abs(maps._bounds(maps._country("Fiji"))[0]) > 170
    manifest = json.loads((maps.ASSETS / "manifest.json").read_text())
    for name, digest in manifest["outputs"].items():
        assert hashlib.sha256((maps.ASSETS / name).read_bytes()).hexdigest() == digest
    assert sum(p.stat().st_size for p in maps.ASSETS.iterdir()) < 5_000_000
    with Image.open(maps.ASSETS / "earth.jpg") as image:
        assert image.size == (4096, 2048)


@pytest.mark.parametrize("factory", [OutlineMap, SatelliteMap, EarthMap])
def test_invalid_arguments(factory):
    for kwargs in ({"latitude": 91}, {"zoom": 0}, {"width": 0}, {"longitude": float("nan")}):
        with pytest.raises(ValueError):
            factory(**kwargs)
    with pytest.raises(ValueError, match="Unknown country"):
        factory().zoom_to("Atlantis")
    with pytest.raises(ValueError):
        factory().zoom_to("Nepal", zoom=-1)


def test_rotation_and_shortest_route_from_timeline_state():
    earth = EarthMap(longitude=170, latitude=-10)
    scene = Scene()
    scene.play(earth.animate.rotate(longitude=360, latitude=20), run_time=1, rate_func=linear)
    scene.play(earth.animate.rotate(longitude=30, latitude=-30), run_time=1)
    entry = scene.entries[0]
    assert entry.state_at(0.5)["longitude"] == 350
    assert entry.state_at(2)["longitude"] == 560
    assert entry.state_at(2)["latitude"] == -20
    scene.play(earth.animate.zoom_to("Pacific Ocean", zoom=2), run_time=1)
    end = entry.state_at(3)
    assert end["longitude"] == 560  # -160 is already centered after a full turn.
    assert end["latitude"] == 0 and end["zoom"] == 2
    assert earth.longitude == 170  # Authoring does not mutate initial state.
    with pytest.raises(ValueError, match="latitude"):
        scene.play(earth.animate.rotate(latitude=100))
    assert scene.time == 3


def test_flat_rotation_and_transform_are_independent():
    c = SatelliteMap(rotation=12).rotate(-30)
    scene = Scene()
    scene.play(c.animate.rotate(90), run_time=1)
    scene.play(c.animate.rotate(-15), run_time=1)
    state = scene.entries[0].state_at(2)
    assert state["map_rotation"] == 45 and state["rotation"] == 12
    with pytest.raises(TypeError):
        c.rotate(longitude=3)
    with pytest.raises(TypeError):
        EarthMap().rotate(3)


def test_missing_dependency_is_actionable(monkeypatch):
    original = builtins.__import__

    def without_numpy(name, *args, **kwargs):
        if name == "numpy":
            raise ImportError("blocked for test")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_numpy)
    earth = EarthMap()
    with pytest.raises(ImportError, match=r"faceless-champ\[maps\]"):
        maps.draw_map(earth, earth.state(), 0.1)


def test_sphere_mask_poles_and_wrapping():
    pytest.importorskip("numpy")
    c = EarthMap(width=120, height=120, longitude=80, latitude=20)
    a = maps.draw_map(c, c.state(), 1)
    assert a.getpixel((0, 0))[3] == 0
    assert a.getpixel((60, 60))[3] == 255
    assert a.getchannel("A").getbbox() == (2, 2, 118, 118)
    c.rotate(longitude=360)
    assert a.tobytes() == maps.draw_map(c, c.state(), 1).tobytes()
    for latitude in [-90, 90]:
        c.latitude = latitude
        assert maps.draw_map(c, c.state(), 1).getpixel((60, 60))[3] == 255
    c.zoom_to("Nepal", zoom=10000)
    assert maps.draw_map(c, c.state(), 1).size == (120, 120)


def test_texture_orientation_and_date_line(monkeypatch):
    np = pytest.importorskip("numpy")
    # Geographic diagnostic texture: red encodes longitude, green latitude.
    texture = np.zeros((180, 360, 3), dtype=np.uint8)
    texture[..., 0] = np.arange(360)[None, :] * 255 / 359
    texture[..., 1] = np.arange(180)[:, None] * 255 / 179
    monkeypatch.setattr(maps, "_texture", lambda: texture)
    c = SatelliteMap(width=360, height=180)
    frame = maps.draw_map(c, c.state(), 1)
    assert frame.getpixel((0, 0)) == (0, 0, 0, 255)
    assert frame.getpixel((359, 179)) == (255, 255, 0, 255)
    c.longitude = 360
    assert frame.tobytes() == maps.draw_map(c, c.state(), 1).tobytes()
    c.longitude = 179
    first = maps.draw_map(c, c.state(), 1)
    c.longitude = -181
    assert first.tobytes() == maps.draw_map(c, c.state(), 1).tobytes()


def test_polygon_holes_and_date_line(monkeypatch):
    pytest.importorskip("numpy")
    country = {
        "name": "Test",
        "aliases": ["Test"],
        "polygons": [
            [
                [[170, -20], [-170, -20], [-170, 20], [170, 20], [170, -20]],
                [[175, -10], [-175, -10], [-175, 10], [175, 10], [175, -10]],
            ]
        ],
    }
    monkeypatch.setattr(maps, "_countries", lambda: [country])
    c = OutlineMap("Test", width=200, height=200, fill="red", border_color=None)
    frame = maps.draw_map(c, c.state(), 1)
    assert frame.getpixel((100, 100))[3] == 0  # Interior hole remains transparent.
    assert frame.getpixel((70, 100)) == (255, 0, 0, 255)
    assert frame.getpixel((0, 100))[3] == 0


def test_renderer_composition_cache_and_animation():
    pytest.importorskip("numpy")
    c = EarthMap(width=90, height=90, position=(60, 50))
    scene = Scene(Canvas(120, 100))
    scene.play(c.animate.rotate(longitude=100), run_time=1)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    first = renderer.frame(scene, 0, (120, 100))
    middle = renderer.frame(scene, 0.5, (120, 100))
    assert first.tobytes() != middle.tobytes()
    assert first.getpixel((0, 0)) == (0, 0, 0, 255)
    assert first.tobytes() == renderer.frame(scene, 0, (120, 100)).tobytes()
