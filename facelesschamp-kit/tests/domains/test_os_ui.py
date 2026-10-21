from copy import deepcopy

import pytest
from faceless_champ import Canvas, Group, PillowRenderer, Scene
from PIL import Image

from facelesschamp_kit.desktop import (
    Control,
    File,
    Folder,
    MacOSPreset,
    OSClip,
    OSScript,
    SettingsPage,
    VirtualFileSystem,
)


def filesystem():
    return VirtualFileSystem(
        Folder(
            "home",
            "Home",
            (
                Folder(
                    "docs",
                    "Documents",
                    (File("note", "Notes.txt", "First line\nSecond line"), Folder("archive", "Archive")),
                ),
                Folder("downloads", "Downloads"),
            ),
        )
    )


def test_filesystem_preserves_identity_and_rejects_invalid_operations():
    fs = filesystem()
    fs.rename("note", "Readme.txt")
    fs.move("note", "archive")
    assert fs.node("note").name == "Readme.txt"
    assert fs.parents["note"] == "archive"
    fs.copy("docs", "downloads", "docs-copy")
    assert fs.parents["docs-copy/note"] == "docs-copy/archive"
    fs.trash("docs")
    assert not fs.visible("note")
    fs.restore("docs")
    assert fs.visible("note")
    for operation in (
        lambda: fs.move("docs", "archive"),
        lambda: fs.trash("home"),
        lambda: fs.rename("note", "../bad"),
        lambda: fs.create_folder("docs", "archive", "Other"),
        lambda: fs.copy("note", "archive", "duplicate", name="Readme.txt"),
    ):
        before = deepcopy(fs.__dict__)
        with pytest.raises(ValueError):
            operation()
        assert fs.__dict__ == before


def test_compiled_snapshots_navigation_and_seek():
    fs = filesystem()
    script = OSScript().open_folder("docs").rename("note", "Readme.txt").drag("note", "archive").open_folder("archive")
    clip = OSClip(fs, script, cursor=False)
    assert clip.state_at(0.59)["folder"] == "home"
    assert clip.state_at(0.6)["folder"] == "docs"
    assert clip.state_at(1.6)["fs"].node("note").name == "Readme.txt"
    assert clip.state_at(2.6)["fs"].parents["note"] == "archive"
    assert clip.state_at(4)["folder"] == "archive"
    assert fs.node("note").name == "Notes.txt"
    script.wait(100)
    assert clip.duration == 4
    snapshot = clip.state_at(4)
    snapshot["fs"].rename("note", "Mutated.txt")
    assert clip.state_at(4)["fs"].node("note").name == "Readme.txt"
    last = clip.frame_image(4, 0.25).tobytes()
    clip.frame_image(0.1, 0.25)
    assert clip.frame_image(4, 0.25).tobytes() == last
    assert len(clip._surface_cache) <= 4


def test_history_search_list_and_explicit_timing():
    script = (
        OSScript()
        .open_folder("docs", at=2)
        .open_folder("archive")
        .back()
        .forward()
        .up()
        .search("Notes")
        .set_view("list")
        .select("note")
    )
    clip = OSClip(filesystem(), script)
    assert clip.state_at(1)["folder"] == "home"
    assert clip.state_at(5)["folder"] == "docs"
    assert clip.state_at(6)["folder"] == "archive"
    assert clip.state_at(script.duration)["selected"] == "note"
    with pytest.raises(ValueError, match="overlap"):
        script.up(at=1)
    with pytest.raises(ValueError):
        OSScript().wait(float("nan"))


@pytest.mark.parametrize(
    "script",
    [
        OSScript().rename("note", "Other.txt"),
        OSScript().rename("note", "Other.txt", cursor=False),
        OSScript().move_cursor("missing"),
        OSScript().open_folder("missing"),
        OSScript().back(),
        OSScript().open_settings().select("note"),
        OSScript().set_value("sound:volume", 50),
        OSScript().window("finder", "resize", size=(100, 100)),
        OSScript().open_folder("docs").drag("note", "missing"),
    ],
)
def test_preflight_invalid_or_hidden_actions(script):
    with pytest.raises(ValueError):
        OSClip(filesystem(), script)


def test_settings_custom_controls_theme_and_typewriter():
    pages = (
        SettingsPage(
            "custom",
            "Custom",
            (
                Control("enabled", "Enabled"),
                Control("name", "Name", "text", ""),
                Control("amount", "Amount", "slider", 10),
                Control("run", "Run", "button", False),
            ),
        ),
    )
    script = (
        OSScript()
        .set_value("custom:enabled", True)
        .type_text("control:custom:name", "Hello")
        .set_value("custom:amount", 90)
        .click("control:custom:run")
    )
    clip = OSClip(script=script, pages=pages, mode="settings", width=1280, height=800)
    values = clip.state_at(4)["values"]
    assert values == {"custom:enabled": True, "custom:name": "Hello", "custom:amount": 90, "custom:run": True}
    assert clip.frame_image(1.45, 0.25).tobytes() != clip.frame_image(2, 0.25).tobytes()
    dark = OSClip(script=OSScript().open_settings().set_value("appearance:theme", "dark"))
    assert dark.state_at(2)["appearance"] == "dark"
    with pytest.raises(ValueError):
        Control("x", "X", "slider", float("inf"))


def test_context_menu_confirmation_and_restore():
    script = (
        OSScript()
        .open_folder("docs")
        .right_click("note")
        .click("menu:preview")
        .window("preview", "close")
        .trash("note", confirm=True)
        .confirm(False)
        .trash("note", confirm=True)
        .confirm()
        .open_trash()
        .restore("note")
        .back()
    )
    clip = OSClip(filesystem(), script)
    assert clip.state_at(5)["dialog"]["id"] == "note"
    assert clip.state_at(6)["fs"].visible("note")
    assert not clip.state_at(8)["fs"].visible("note")
    assert clip.state_at(11)["fs"].visible("note")
    assert clip.state_at(11)["folder"] == "docs"


def test_windows_focus_geometry_interpolation_and_restore():
    script = (
        OSScript()
        .window("finder", "move", position=(100, 100))
        .window("finder", "resize", size=(1050, 700))
        .window("finder", "maximize")
        .window("finder", "restore")
        .window("finder", "minimize")
        .window("finder", "restore")
    )
    clip = OSClip(filesystem(), script)
    start = clip.bounds_for("finder:title", 0)
    middle = clip.bounds_for("finder:title", 0.6)
    end = clip.bounds_for("finder:title", 1)
    assert start.left < middle.left < end.left
    assert clip.state_at(4)["windows"]["finder"]["box"] == (100, 100, 1050, 700)
    assert clip.state_at(5)["windows"]["finder"]["minimized"]
    assert not clip.state_at(6)["windows"]["finder"]["minimized"]


def test_scroll_long_names_and_target_visibility():
    fs = VirtualFileSystem(
        Folder("root", "Home", tuple(File(f"f{i}", f"{i} " + "Long filename " * 10) for i in range(90)))
    )
    clip = OSClip(fs, OSScript().scroll(50).select("f89"))
    with pytest.raises(ValueError, match="visible"):
        clip.bounds_for("f89", 0)
    assert clip.bounds_for("f89", 2).bottom < clip.height
    assert clip.frame_image(0.6, 0.25).size == (480, 270)


@pytest.mark.parametrize("view", ["list", "icons"])
@pytest.mark.parametrize("rows", [0, 30, 150, 10000])
def test_large_folder_scroll_renders_inside_track(view, rows, monkeypatch):
    from facelesschamp_kit.desktop.drawing import Painter

    fs = VirtualFileSystem(Folder("root", "Files", tuple(File(f"f{i}", f"File {i:03}.txt") for i in range(200))))
    clip = OSClip(
        fs,
        OSScript().set_view(view, duration=0.1).scroll(rows, duration=0.1),
        mode="finder",
        width=1280,
        height=800,
        cursor=False,
    )
    original = Painter.rect
    thumbs = []

    def checked(painter, box, fill, radius=8, outline=None, width=1):
        if radius == 3 and fill == painter.colors["muted"]:
            _, top, _, bottom = box
            track = clip.bounds_for("finder:content", 0.19)
            assert track.top <= top <= bottom <= track.bottom
            thumbs.append((top, bottom))
        return original(painter, box, fill, radius, outline, width)

    monkeypatch.setattr(Painter, "rect", checked)
    for at in (0.19, 0.05, 0.15, 0.19):
        assert clip.frame_image(at, 0.25).size == (320, 200)
    assert thumbs


def test_isolated_transparency_group_transform_and_excerpt_cache():
    fs = filesystem()
    script = OSScript().open_folder("docs").rename("note", "Readme.txt")
    clip = OSClip(fs, script, mode="finder", width=1280, height=800, position=(640, 400))
    assert clip.frame_image(0).getpixel((0, 0))[3] == 0
    excerpt = OSClip(fs, script, mode="finder", width=1280, height=800, source_start=1.2)
    assert clip.frame_image(1.5, 0.25).tobytes() == excerpt.frame_image(0.3, 0.25).tobytes()
    group = Group(clip)
    scene = Scene(Canvas(1280, 800)).add(group)
    scene.play(group.animate.scale_to(0.8).rotate_to(4), run_time=1).wait(1)
    renderer = PillowRenderer(1)
    at_end = renderer.frame(scene, 1.9, (640, 400)).tobytes()
    assert at_end != renderer.frame(scene, 0.1, (640, 400)).tobytes()
    assert at_end == renderer.frame(scene, 1.9, (640, 400)).tobytes()


def test_image_preview_assets_are_loaded_and_packaged_fonts_work(tmp_path):
    asset = tmp_path / "image.png"
    Image.new("RGB", (80, 80), "red").save(asset)
    fs = VirtualFileSystem(Folder("root", "Home", (File("image", "Image.png", image=asset),)))
    clip = OSClip(fs, OSScript().preview("image"), preset=MacOSPreset(appearance="dark"))
    asset.unlink()
    image = clip.frame_image(1, 0.25)
    pixels = image.tobytes()
    assert any(pixels[i] > 240 and pixels[i + 1] < 20 and pixels[i + 2] < 20 for i in range(0, len(pixels), 4))


def test_action_typos_and_nonfinite_controls_fail_early():
    with pytest.raises(TypeError, match="Unexpected"):
        OSScript().open_folder("docs", duraton=2)
    with pytest.raises(ValueError):
        OSScript().open_folder(123)
    with pytest.raises(ValueError):
        Control("x", "X", "slider", 10, maximum=float("inf"))
    with pytest.raises(ValueError):
        OSClip().bounds_for(None)


def test_preset_typography_size_changes_rendered_labels():
    normal = OSClip(filesystem(), cursor=False)
    larger = OSClip(filesystem(), cursor=False, preset=MacOSPreset(font_size=28))
    assert normal.frame_image(0, 0.25).tobytes() != larger.frame_image(0, 0.25).tobytes()
    with pytest.raises(ValueError, match="font_size"):
        MacOSPreset(font_size=100)


def test_off_canvas_desktop_targets_are_unavailable():
    fs = VirtualFileSystem(Folder("root", "Home", tuple(Folder(f"folder{i}", f"Folder {i}") for i in range(6))))
    script = OSScript().window("finder", "close").double_click("desktop:folder5")
    with pytest.raises(ValueError, match="hidden"):
        OSClip(fs, script, width=980, height=690)
