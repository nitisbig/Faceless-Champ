import json

import pytest
from PIL import Image

from faceless_champ import Canvas, Group, PillowRenderer, Scene
from faceless_champ.web import HtmlClip, HtmlPage, WebCapture, WebError, WebScript
from faceless_champ.web.capture import input_digest


def prepared(tmp_path):
    for i, color in enumerate(("red", "blue")):
        Image.new("RGBA", (100, 60), color).save(tmp_path / f"{i:08d}.png")
    metadata = {"geometry": {"#box": [10, 10, 40, 40]}, "cursor": [0, 0], "clicks": []}
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {"schema": 1, "fps": 2, "duration": 1, "viewport": [100, 60], "frames": {"0": metadata, "1": metadata}}
        )
    )
    return WebCapture(tmp_path)


def test_action_contract():
    script = WebScript(3).type("#input", "hello", at=0, duration=1).click("#send", at=1)
    assert len(script.actions) == 2
    for call in (
        lambda: script.click("#x", at=0.5),
        lambda: script.click("#x", at=3),
        lambda: WebScript(float("nan")),
        lambda: script.track(""),
    ):
        with pytest.raises(ValueError):
            call()


def test_hash_changes_with_assets(tmp_path):
    path = tmp_path / "index.html"
    path.write_text("<h1>Hello</h1>")
    page = HtmlPage(path)
    before = input_digest(page)
    (tmp_path / "style.css").write_text("h1 {color:red}")
    assert input_digest(page) != before
    after = input_digest(page)
    (tmp_path / ".web-cache").mkdir()
    (tmp_path / ".web-cache" / "generated").write_text("ignored")
    assert input_digest(page) == after


def test_clip_seek_crop_group_and_cache(tmp_path):
    capture = prepared(tmp_path)
    clip = HtmlClip(capture, width=100, height=60, position=(100, 60))
    scene = Scene(Canvas(200, 120))
    scene.add(Group(clip))
    scene.wait(2)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0, (200, 120)).getpixel((100, 60))[:3] == (255, 0, 0)
    assert renderer.frame(scene, 0.5, (200, 120)).getpixel((100, 60))[:3] == (0, 0, 255)
    assert renderer.frame(scene, 1.8, (200, 120)).getpixel((100, 60))[:3] == (0, 0, 255)
    assert renderer.frame(scene, 0, (200, 120)).getpixel((100, 60))[:3] == (255, 0, 0)
    cropped = HtmlClip(capture, width=30, height=30, selector="#box", source_start=0.5)
    assert cropped.frame_image(0).getpixel((15, 15))[:3] == (0, 0, 255)
    assert len(renderer._sprites) == 0  # HTML frames never accumulate in sprite caches.
    assert clip.bounds.width == 100


def test_missing_range_and_incomplete_capture(tmp_path):
    capture = prepared(tmp_path)
    del capture.frames["0"]
    with pytest.raises(WebError, match="not prepared"):
        capture.image(0)
    (tmp_path / "00000001.png").unlink()
    with pytest.raises(WebError, match="Incomplete"):
        WebCapture(tmp_path)


@pytest.mark.skipif(__import__("os").environ.get("FC_WEB_BROWSER_TESTS") != "1", reason="opt-in Chromium integration")
def test_browser_timing_and_ranges(tmp_path):
    from faceless_champ.web import capture_html

    html = tmp_path / "index.html"
    html.write_text("""<style>body{margin:0} #box{width:80px;height:80px;background:red;transition:width 1s linear}
      #scroll{width:100px;height:30px;overflow:auto}</style>
      <input id="input"><button id="go" onclick="document.querySelector('#box').style.width='180px';
      setTimeout(()=>document.querySelector('#box').style.background='blue',500)">Go</button>
      <select id="select"><option>a</option><option>b</option></select><div id="box"></div>
      <div id="scroll"><div style="height:200px">scroll</div></div>""")
    Image.new("RGB", (5, 5), "green").save(tmp_path / "asset.png")
    with html.open("a") as stream:
        stream.write(
            '<img src="asset.png"><div id="animated"></div><style>'
            "#animated{position:absolute;top:200px;width:10px;height:10px;background:green;"
            "animation:slide 2s linear infinite}@keyframes slide{to{transform:translateX(100px)}}"
            "</style>"
        )
    script = WebScript(2).type("#input", "hi", at=0, duration=0.2).click("#go", at=0.3)
    script.select("#select", "b", at=0.4).scroll("#scroll", at=0.5, y=100, duration=0.2)
    script.track("#box", "#animated")
    page = HtmlPage(html, viewport=(320, 240))
    cache = tmp_path / ".web-cache"
    full = capture_html(page, script, fps=10, cache_dir=cache)
    assert 115 < full.metadata(0.8)["geometry"]["#box"][2] < 140
    ranged = capture_html(page, script, fps=10, cache_dir=cache, start_time=0.8, end_time=1.2)
    for time in (0.8, 0.9, 1.0, 1.1):
        assert full.image(time).tobytes() == ranged.image(time).tobytes()
    repeat = capture_html(page, script, fps=10, cache_dir=tmp_path / "output" / "repeat")
    assert repeat.image(0.9).tobytes() == full.image(0.9).tobytes()
    assert full.metadata(1)["geometry"]["#animated"][0] > full.metadata(0)["geometry"]["#animated"][0]
    assert not list(cache.glob(".preparing-*"))
    with pytest.raises(WebError, match="expected one target"):
        capture_html(page, WebScript(1).click("#missing", at=0), cache_dir=cache)
    assert not list(cache.glob(".preparing-*"))


def test_fractional_duration_final_frame(tmp_path):
    capture = prepared(tmp_path)
    capture.duration = 0.75
    clip = HtmlClip(capture, width=100, height=60)
    assert clip.frame_image(3).getpixel((10, 10))[:3] == (0, 0, 255)


def test_optional_browser_dependency_error(tmp_path, monkeypatch):
    import builtins

    from faceless_champ.web import capture_html

    path = tmp_path / "ui.html"
    path.write_text("<p>Hi</p>")
    original = builtins.__import__

    def without_browser(name, *args, **kwargs):
        if name.startswith("playwright"):
            raise ImportError("intentionally absent")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_browser)
    with pytest.raises(WebError, match="faceless-champ\\[web\\]"):
        capture_html(HtmlPage(path), WebScript(1), cache_dir=tmp_path / ".web-cache")


def test_multiple_clips_with_transforms(tmp_path):
    capture = prepared(tmp_path)
    first = HtmlClip(capture, width=80, height=40, position=(50, 50), rotation=20, opacity=0.7)
    second = HtmlClip(capture, width=80, height=40, position=(150, 50), source_start=0.5)
    group = Group(first)
    group.scale_x = 0.8
    scene = Scene(Canvas(200, 100))
    scene.add(group, second)
    scene.wait(1)
    renderer = PillowRenderer(1)
    before = renderer.frame(scene, 0, (200, 100))
    after = renderer.frame(scene, 0.5, (200, 100))
    assert before.getpixel((50, 50)) != after.getpixel((50, 50))
    assert before.getpixel((150, 50))[:3] == (0, 0, 255)
    assert before.tobytes() == renderer.frame(scene, 0, (200, 100)).tobytes()


def test_masked_html_clip(tmp_path):
    from faceless_champ import CircleMask

    capture = prepared(tmp_path)
    clip = HtmlClip(capture, width=100, height=60, position=(50, 30), mask=CircleMask(20))
    scene = Scene(Canvas(100, 60, "#00000000")).add(clip).wait(1)
    frame = PillowRenderer(1).frame(scene, 0, (100, 60))
    assert frame.getpixel((50, 30))[:3] == (255, 0, 0)
    assert frame.getpixel((0, 0))[3] == 0


def test_truncated_capture_is_not_complete(tmp_path):
    prepared(tmp_path)
    (tmp_path / "00000000.png").write_bytes(b"partial")
    with pytest.raises(WebError, match="Incomplete capture"):
        WebCapture(tmp_path)
