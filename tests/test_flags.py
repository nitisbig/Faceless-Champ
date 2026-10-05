from pathlib import Path

import pytest
from PIL import Image as PILImage

from faceless_champ import Canvas, FadeIn, Flag, Image, PillowRenderer, Scene, flag_path, linear, supported_flags


@pytest.mark.parametrize("code", ["np", "NP", " np ", "US", "gb-eng", "GB-SCT", "xk"])
def test_code_lookup_is_case_insensitive_and_independent_of_cwd(code, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = flag_path(code)
    assert path.is_absolute() and path.is_file()
    assert path.name == f"{code.strip().lower()}.png"
    flag = Flag(code)
    assert isinstance(flag, Image)
    assert flag.path == path and flag.country_code == path.stem


def test_bundled_assets_are_complete_and_valid():
    codes = supported_flags()
    assert len(codes) == 254
    assert codes == tuple(sorted(set(codes)))
    assert {"np", "us", "xk", "gb-eng", "gb-nir", "gb-sct", "gb-wls"} <= set(codes)
    for code in codes:
        path = flag_path(code)
        with PILImage.open(path) as image:
            assert image.format == "PNG"
            image.verify()


@pytest.mark.parametrize("code", ["", "zz", "Nepal", "np.png", "../np", "/tmp/np", "gb/eng"])
def test_unknown_codes_fail_with_lookup_guidance(code):
    for lookup in (flag_path, Flag):
        with pytest.raises(ValueError, match="supported_flags"):
            lookup(code)


@pytest.mark.parametrize("code", [None, 123, b"np", Path("np")])
def test_codes_must_be_strings(code):
    for lookup in (flag_path, Flag):
        with pytest.raises(TypeError, match="country_code"):
            lookup(code)


def test_flag_render_preserves_colors_transparency_fitting_and_animation():
    flag = Flag("np", width=120, height=120, position=(80, 80))
    scene = Scene(Canvas(160, 160, "#123456"))
    scene.play(FadeIn(flag), run_time=1, rate_func=linear)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    start = renderer.frame(scene, 0, (160, 160))
    middle = renderer.frame(scene, 0.5, (160, 160))
    end = renderer.frame(scene, 1, (160, 160))
    reference = Scene(scene.canvas)
    reference.add(Image(flag_path("np"), width=120, height=120, position=(80, 80))).wait(1)
    assert end.tobytes() == renderer.frame(reference, 0, (160, 160)).tobytes()
    assert start.getpixel((80, 80)) == (18, 52, 86, 255)
    assert start.tobytes() != middle.tobytes() != end.tobytes()
    assert end.getpixel((21, 21)) == (18, 52, 86, 255)  # Transparent fitting margins.
    colors = end.getcolors(end.width * end.height)
    assert any(r > 150 and g < 100 and b < 120 for count, (r, g, b, a) in colors)  # Original red.


def test_flag_accepts_image_options_and_component_transforms():
    flag = Flag("ch", width=60, height=40, fit="cover", trim=True, position=(50, 50), rotation=30)
    scene = Scene(Canvas(100, 100))
    scene.add(flag)
    scene.play(flag.animate.move_to(60, 40).scale_to(0.5), run_time=1, rate_func=linear)
    assert scene.entries[0].state_at(1)["position"] == (60, 40)
    assert scene.entries[0].state_at(1)["scale"] == 0.5
    image = PillowRenderer(1).frame(scene, 1, (100, 100))
    assert image.getpixel((60, 40))[:3] == (255, 255, 255)
