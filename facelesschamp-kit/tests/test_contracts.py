import json
import wave

import pytest
from faceless_champ import Bounds, Canvas, Circle, PillowRenderer, Text

from facelesschamp_kit import BuildContext, KitError, Project, Video
from facelesschamp_kit.assets import AssetRegistry, digest
from facelesschamp_kit.blocks import Comparison, Heading, ImageCard, MetricCard, StepList, TextPanel
from facelesschamp_kit.cli import main
from facelesschamp_kit.layouts import Stack
from facelesschamp_kit.scaffold import init_project
from facelesschamp_kit.themes import LIGHT, MIDNIGHT


@pytest.fixture
def ctx(tmp_path):
    return BuildContext(tmp_path)


def audio_files(root, seconds=3):
    audio = root / "voice.wav"
    with wave.open(str(audio), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(8000)
        f.writeframes(b"\0\0" * int(8000 * seconds))
    srt = root / "cues.srt"
    srt.write_text("7\n00:00:00,000 --> 00:00:00,500\nHello\n\n19\n00:00:01,000 --> 00:00:02,000\nWorld\n")
    return audio, srt


def test_timing_styles_and_lifetimes(ctx):
    video = Video(ctx)
    video.segment("later", start=3, duration=2).add(Heading("Later"))
    first = video.segment("first", start=0, duration=3)
    first.add(Heading("First"))
    assert video.segment("append", duration=1).start == 5
    compiled = video.compile()
    scene = compiled.composition
    assert scene.duration == 6
    assert [(e.start, e.end) for e in scene.entries] == [(0, 3), (3, 5)]
    assert scene.entries[0].end == scene.entries[1].start


def test_independent_placements_and_builds(ctx):
    video = Video(ctx)
    block = MetricCard(42, "Reusable")
    video.segment("one", duration=2).add(block)
    video.segment("two", duration=2).add(block)
    a, b = video.compile(), video.compile()
    aa, bb = a.composition.entries, b.composition.entries
    assert not {id(e.component) for e in aa} & {id(e.component) for e in bb}
    assert len({id(e.component) for e in aa}) == len(aa)


def test_reused_raw_instances_rejected(ctx):
    item = Circle(position=ctx.bounds.center)
    video = Video(ctx)
    video.segment("one", duration=2).add_core(lambda ctx, bounds: item)
    first = video.compile()
    with pytest.raises(KitError, match="OWNERSHIP"):
        video.compile()
    assert first.duration == 2


def test_raw_factory_and_custom_child_motion(ctx):
    video = Video(ctx)
    segment = video.segment("one", start=5, duration=3)
    handle = segment.add(MetricCard(1, "Count"))
    segment.play(handle["value"], lambda c: c.animate.value_to(10), at=1, duration=1)
    result = video.compile()
    entry = next(e for e in result.composition.entries if e.tracks)
    assert entry.tracks[0].start == 6
    assert entry.state_at(7)["value"] == 10


def test_conflicts_and_retry(ctx):
    video = Video(ctx)
    segment = video.segment("one", duration=3)
    handle = segment.add(Heading("Title"), enter="fade", enter_duration=1)
    segment.play(handle, lambda c: c.animate.opacity_to(0.5), at=0.5, duration=1)
    with pytest.raises(KitError, match="TIMELINE"):
        video.compile()
    segment.motions.clear()
    assert video.compile().duration == 3


def test_stagger_stays_hidden_before_entry(ctx):
    video = Video(ctx)
    video.segment("one", duration=3).add(StepList(("First", "Second", "Third")), enter="stagger")
    scene = video.compile().composition
    animated = [e for e in scene.entries if e.tracks]
    assert len(animated) == 3
    assert animated[1].state_at(0)["opacity"] == 0
    assert animated[2].state_at(0.05)["opacity"] == 0
    assert animated[2].state_at(1)["opacity"] == 1


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf"), True])
def test_bad_durations(ctx, duration):
    with pytest.raises(KitError):
        Video(ctx).segment("bad", duration=duration)


def test_window_overflow_and_unknown_child(ctx):
    video = Video(ctx)
    segment = video.segment("one", duration=1)
    handle = segment.add(Heading("Title"))
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        segment.play(handle, lambda c: c.animate.opacity_to(0), duration=2)
    segment.play(handle["missing"], lambda c: c.animate.opacity_to(0))
    with pytest.raises(KitError, match="HANDLE"):
        video.compile()


@pytest.mark.parametrize("size", [(1080, 1920), (1920, 1080)])
@pytest.mark.parametrize("theme", [MIDNIGHT, LIGHT])
@pytest.mark.parametrize(
    "block",
    [
        Heading("Clear reusable headings"),
        TextPanel("A concise explanation.", "Context"),
        MetricCard(42, "Reusable components"),
        ImageCard("missing", mode="placeholder"),
        Comparison("Before", "After"),
        StepList(("Compose", "Preview", "Export")),
    ],
)
def test_catalog_formats_and_themes(tmp_path, size, theme, block):
    context = BuildContext(tmp_path, Canvas(*size, theme.background), theme)
    video = Video(context)
    video.segment("one", duration=2).add(block)
    result = video.compile()
    frame = PillowRenderer(1).frame(result.composition, 1, (192, 108) if size[0] > size[1] else (108, 192))
    assert frame.getbbox()


def test_text_overflow(ctx):
    with pytest.raises(KitError, match="TEXT_FIT"):
        Heading("enormousword" * 100).compose(ctx, Bounds(0, 0, 60, 40))


def test_layout_before_snapshot(ctx):
    video = Video(ctx)
    video.segment("one", duration=2).add(Stack(Heading("First"), Heading("Second")))
    scene = video.compile().composition
    children = [e for e in scene.entries if isinstance(e.component, Text)]
    assert children[0].initial["position"][1] < children[1].initial["position"][1]


def test_assets_required_placeholder_checksum_and_changed_file(tmp_path):
    registry = AssetRegistry(tmp_path, {"image": {"type": "image", "path": "image.png"}})
    with pytest.raises(KitError, match="ASSET_MISSING"):
        registry.image("image")
    assert registry.image("image", "auto") is None
    path = tmp_path / "image.png"
    path.write_bytes(b"first")
    assert registry.image("image") == path
    first = registry.resolved["image:required"]["checksum"]
    path.write_bytes(b"second")
    registry.image("image")
    assert registry.resolved["image:required"]["checksum"] != first
    registry.entries["image"]["checksum"] = first
    with pytest.raises(KitError, match="ASSET_CHECKSUM"):
        registry.image("image")


def test_pack_resource_materialization(tmp_path, monkeypatch):
    package = tmp_path / "pack"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "data.bin").write_bytes(b"packaged")
    monkeypatch.syspath_prepend(str(tmp_path))
    registry = AssetRegistry(tmp_path, {"image": {"type": "image", "package": "pack", "resource": "data.bin"}})
    resolved = registry.image("image")
    (package / "data.bin").unlink()
    assert resolved.read_bytes() == b"packaged"
    assert digest(resolved) == registry.resolved["image:required"]["checksum"]


def test_narration_windows_tail_and_captions(ctx, tmp_path):
    audio, srt = audio_files(tmp_path)
    video = Video(ctx)
    voice = video.narration(audio=audio, subtitles=srt, markers={"hello": 7, "world": 19}, captions=True)
    first = voice.between("hello", "world")
    assert (first.start, first.end, first.cues) == (0, 1, (7, 19))
    video.segment("one", window=first).add(Heading("Hello"))
    video.segment("two", start=1, duration=1).add(Heading("World"))
    result = video.compile()
    assert result.duration == 3
    assert result.report["segments"][-1]["end"] == 3
    assert result.report["diagnostics"][0]["code"] == "AUDIO_TAIL_HOLD"
    assert result.composition.audio[0].start == 0
    assert result.report["narration"]["cues"][1]["start"] == 1
    assert ctx.bounds.bottom == 1920 - 64 - 220


def test_reject_cues_beyond_audio(ctx, tmp_path):
    audio, srt = audio_files(tmp_path, seconds=1)
    with pytest.raises(KitError, match="CUE_AUDIO"):
        Video(ctx).narration(audio=audio, subtitles=srt, markers={"hello": 7})


def test_project_scaffold_cli_and_cwd(tmp_path, monkeypatch, capsys):
    project = init_project(tmp_path / "project")
    monkeypatch.chdir(tmp_path)
    assert Project(project).validate()["duration"] == 10
    assert main(["--project", str(project), "inspect", "main", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["video"] == "main" and len(report["fingerprint"]) == 64
    assert main(["--project", str(project), "inspect", "bad", "--json"]) == 1
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "VIDEO_ID"
    with pytest.raises(KitError, match="DESTINATION"):
        init_project(project)


def test_config_unknown_fields_and_bad_profile(tmp_path):
    root = init_project(tmp_path / "p")
    cfg = root / "facelesschamp.toml"
    cfg.write_text(cfg.read_text() + "\nunknown = 12\n")
    with pytest.raises(KitError, match="Unknown fields"):
        Project(root)


def test_two_projects_no_module_leak(tmp_path):
    a, b = init_project(tmp_path / "a"), init_project(tmp_path / "b")
    p = b / "videos/main.py"
    p.write_text(p.read_text().replace("duration=3", "duration=4"))
    assert Project(a).build().duration == 10
    assert Project(b).build().duration == 12
    assert Project(a).build().duration == 10


def test_core_authored_entry(tmp_path):
    root = init_project(tmp_path / "p")
    (root / "videos/main.py").write_text(
        "from faceless_champ import Scene, Text\n"
        'def build(ctx):\n    s=Scene(ctx.canvas)\n    s.add(Text("Core", position=ctx.bounds.center))\n'
        "    s.wait(2)\n    return s\n"
    )
    report = Project(root).validate()
    assert report["authoring"] == "core" and report["duration"] == 2


def test_strict_assets(tmp_path):
    root = init_project(tmp_path / "p")
    (root / "videos/main.py").write_text(
        "from facelesschamp_kit import Video\n"
        "from facelesschamp_kit.blocks import ImageCard\n"
        "def build(ctx):\n    v=Video(ctx)\n"
        '    v.segment("one",duration=2).add(ImageCard("missing",mode="placeholder"))\n    return v\n'
    )
    assert Project(root).validate()["assets"][0]["placeholder"]
    with pytest.raises(KitError, match="ASSET_PLACEHOLDER"):
        Project(root).validate(strict_assets=True)


def test_minimum_font_and_long_label_wrap(ctx):
    box = Bounds(0, 0, 420, 400)
    result = Heading("A longer sentence that should wrap without cropping").compose(ctx, box)
    assert "\n" in result.root.text
    assert result.root.font_size >= ctx.theme.minimum_font_size
    assert result.root.bounds.width <= box.width


def test_duplicate_manifest_keys(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/manifest.json").write_text('{"x": {}, "x": {}}')
    with pytest.raises(KitError, match="Duplicate"):
        AssetRegistry(tmp_path)


def test_stable_seed_and_style_precedence(ctx):
    from dataclasses import replace

    ctx.theme = replace(ctx.theme, accent="#FF0000")
    assert Heading("Theme", variant="accent").compose(ctx, ctx.bounds).root.color == "#FF0000"
    assert Heading("Explicit", variant="accent", color="#00FF00").compose(ctx, ctx.bounds).root.color == "#00FF00"
    other = BuildContext(ctx.root, seed=ctx.seed)
    assert ctx.random.random() == other.random.random()


def test_final_export_rejects_placeholder_before_ffmpeg(tmp_path):
    root = init_project(tmp_path / "p")
    (root / "videos/main.py").write_text(
        "from facelesschamp_kit import Video\n"
        "from facelesschamp_kit.blocks import ImageCard\n"
        "def build(ctx):\n    v=Video(ctx)\n"
        '    v.segment("one",duration=2).add(ImageCard("missing",mode="placeholder"))\n    return v\n'
    )
    with pytest.raises(KitError, match="ASSET_PLACEHOLDER"):
        Project(root).export("main", root / "output.mp4")
    assert not (root / "output.mp4").exists()


def test_preview_segment_uses_source_times(tmp_path, monkeypatch):
    import facelesschamp_kit.project as service

    root = init_project(tmp_path / "p")
    observed = {}

    def render(node, output, **kwargs):
        observed.update(kwargs)
        return output

    monkeypatch.setattr(service, "render", render)
    monkeypatch.setattr(service, "probe", lambda path: {})
    Project(root).export("main", root / "part.mp4", preview=True, segment="comparison")
    assert (observed["start_time"], observed["end_time"]) == (3, 7)


def test_bad_profile_aspect_and_unknown_profile(tmp_path):
    root = init_project(tmp_path / "p")
    project = Project(root)
    project.config["profiles"]["preview"].update(width=640, height=480)
    with pytest.raises(ValueError, match="aspect"):
        project.validate()
    with pytest.raises(KitError, match="PROFILE"):
        project.settings(project.build(), "missing")


def test_named_children_must_belong_to_root(ctx):
    from facelesschamp_kit import BlockBuild

    class Invalid:
        def compose(self, context, bounds):
            return BlockBuild(Circle(position=bounds.center), {"rogue": Circle()})

    video = Video(ctx)
    video.segment("one", duration=1).add(Invalid())
    with pytest.raises(KitError, match="BLOCK_CONTRACT"):
        video.compile()


def test_scaffold_narration_is_runnable_and_labeled(tmp_path):
    root = init_project(tmp_path / "p", "narrated-short")
    report = Project(root).validate()
    assert report["duration"] == 30
    assert report["segments"][0]["id"] == "sample-label"
    assert all(a["checksum"] for a in report["assets"])


def test_custom_example(tmp_path):
    import runpy
    from pathlib import Path

    factory = runpy.run_path(str(Path(__file__).parents[1] / "examples/custom_block.py"))["build"]
    result = factory(BuildContext(tmp_path)).compile()
    assert result.duration == 6


def test_entrance_preserves_later_fade_target(ctx):
    from faceless_champ import FadeIn

    video = Video(ctx)
    segment = video.segment("one", duration=3)
    handle = segment.add(Heading("Hello"), enter="fade")
    segment.play(handle, FadeIn, at=1, duration=1)
    scene = video.compile().composition
    assert scene.entries[0].state_at(2)["opacity"] == 1


def test_narrated_sample_captions_fit_without_retiming(tmp_path):
    from faceless_champ import Captions

    root = init_project(tmp_path / "p", "narrated-short")
    project = Project(root)
    project.config["videos"]["main"]["captions"] = True
    compiled = project.build()
    captions = next(e for e in compiled.composition.entries if isinstance(e.component, Captions))
    assert captions.start == 0
    assert captions.component.bounds.height <= compiled.context.caption_space
    assert [c.start for c in captions.component.track.cues] == [0, 10, 20]


def test_real_image_asset_and_frame(tmp_path):
    from PIL import Image

    path = tmp_path / "image.png"
    Image.new("RGB", (40, 20), "red").save(path)
    ctx = BuildContext(tmp_path, assets=AssetRegistry(tmp_path, {"photo": {"type": "image", "path": "image.png"}}))
    video = Video(ctx)
    video.segment("one", duration=1).add(ImageCard("photo"))
    frame = PillowRenderer(1).frame(video.compile().composition, 0.5, (108, 192))
    assert frame.getpixel((54, 96))[:3] == (255, 0, 0)


def test_export_range_rejects_ambiguous_request(tmp_path):
    root = init_project(tmp_path / "p")
    with pytest.raises(KitError, match="RANGE"):
        Project(root).export("main", root / "part.mp4", preview=True, segment="hook", start=0, end=1)
    with pytest.raises(KitError, match="RANGE"):
        Project(root).export("main", root / "part.mp4", preview=True, start=0)


def test_frame_overwrite_protection(tmp_path):
    root = init_project(tmp_path / "p")
    output = root / "frame.png"
    project = Project(root)
    project.frame("main", 1, output)
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        project.frame("main", 2, output)
    assert output.read_bytes() == before


def test_many_segments_streamable(ctx):
    video = Video(ctx)
    for index in range(100):
        video.segment(str(index), duration=1).add(Heading(str(index)))
    compiled = video.compile()
    assert compiled.duration == 100
    renderer = PillowRenderer(1, frame_cache_mb=1)
    last = renderer.frame(compiled.composition, 99.5, (108, 192))
    first = renderer.frame(compiled.composition, 0.5, (108, 192))
    assert last.tobytes() != first.tobytes()
