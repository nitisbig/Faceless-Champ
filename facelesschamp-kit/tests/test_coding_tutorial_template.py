"""Approved geometry and hackable style data, without rendering tutorial media."""

import json
from importlib.resources import files

import pytest
from faceless_champ import Bounds, PillowRenderer

from facelesschamp_kit import CodingTutorialStyle, CodingTutorialTemplate, KitError


def test_template_composes_inside_kit_safe_bounds_without_stretching(tmp_path):
    from faceless_champ import Canvas

    from facelesschamp_kit import BuildContext, Video

    video = Video(BuildContext(tmp_path, canvas=Canvas(1920, 1080)))

    def factory(ctx, bounds):
        template = CodingTutorialTemplate()
        editor, _, _ = template.editor("value = 1", language="text")
        return template.group(editor, bounds=bounds)

    video.segment("lesson", duration=3).add_core(factory, enter=None, exit=None)
    compiled = video.compile()
    assert compiled.duration == 3
    box = compiled.composition.entries[0].component.bounds
    assert box.left >= 63 and box.right <= 1857 and box.top >= 63 and box.bottom <= 1017


def test_bundled_style_preserves_the_approved_design_and_fresh_hierarchies(monkeypatch):
    monkeypatch.setattr(PillowRenderer, "frame", lambda *args, **kwargs: pytest.fail("No scene render expected"))
    style = CodingTutorialStyle.load()
    assert style == CodingTutorialStyle()
    assert files("facelesschamp_kit.tutorials.coding").joinpath("TEMPLATE.md").is_file()
    template = CodingTutorialTemplate(style)
    assert template.workspace.editor_full == Bounds(96, 108, 1824, 972)
    assert template.workspace.editor_scale == 0.64
    first, code, caret = template.editor('print("Lesson")', language="text")
    second, other_code, _ = template.editor("x = 1", filename="other.py", language="text")
    assert first is not second and code is not other_code
    assert code in first.children and caret in first.children
    assert code.reveal == 0 and first.scale == 0.96
    assert template.finder("lesson.py").preset.font
    assert not any(node.label for node in template.flow().graph.nodes)


@pytest.mark.parametrize("kind", ["editor", "terminal"])
def test_template_code_is_actually_hidden_before_typing(kind):
    from facelesschamp_kit.coding import CodeReveal
    from faceless_champ import Scene

    template = CodingTutorialTemplate()

    def window_for(source):
        result = template.editor(source, language="text") if kind == "editor" else template.terminal(source)
        window, code = result[:2]
        window.opacity = 1
        return window, code

    window, code = window_for("Hello")
    scene = Scene(template.canvas()).add(window).wait(1)
    empty, _ = window_for("")
    reference = Scene(template.canvas()).add(empty).wait(1)
    with PillowRenderer(1) as renderer:
        assert scene._objects[code].initial["reveal"] == 0
        assert renderer.frame(scene, 0.5, (960, 540)).tobytes() == renderer.frame(reference, 0.5, (960, 540)).tobytes()
        scene.play(CodeReveal(code), run_time=1)
        assert renderer.frame(scene, 1.9, (960, 540)).tobytes() != renderer.frame(reference, 0.5, (960, 540)).tobytes()


def test_editable_json_changes_the_whole_color_system_and_layout(tmp_path):
    path = tmp_path / "style.json"
    path.write_text(
        json.dumps(
            {
                "background": "#123456",
                "accent": "#44CC88",
                "editor_background": "#151515",
                "inset_x": 120,
                "code_size": 48,
            }
        )
    )
    template = CodingTutorialTemplate(CodingTutorialStyle.load(path))
    assert template.canvas().bg == "#123456"
    assert template.finder("main.py").preset.wallpaper == "#123456"
    assert template.finder("main.py").preset.accent == "#44CC88"
    window, code, caret = template.editor("value = 1", language="text")
    assert template.workspace.bounds.left == 120 and code.font_size == pytest.approx(38.4)
    assert caret.fill == "#44CC88"
    assert window.theme.background == "#151515" and window.theme.accent == "#44CC88"
    assert template.flow().theme.accent == "#44CC88"
    assert template.style.palette["background"] == "#123456"
    assert CodingTutorialStyle().background == "#E8E6E2"


@pytest.mark.parametrize(
    "data",
    [{"background": "invalid"}, {"code_size": 0}, {"editor_scale": 0.99}, {"inset_x": 1000}, {"unknown": True}, []],
)
def test_invalid_styles_fail_with_actionable_diagnostics(tmp_path, data):
    path = tmp_path / "style.json"
    path.write_text(json.dumps(data))
    with pytest.raises(KitError, match="TUTORIAL_STYLE"):
        CodingTutorialStyle.load(path)
