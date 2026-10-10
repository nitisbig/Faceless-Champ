"""Behavioral contracts for reusable code editors (no FFmpeg dependency)."""

import builtins
from copy import deepcopy
from dataclasses import replace

import pytest

from faceless_champ import (
    Canvas,
    CodeReveal,
    CodeTheme,
    CodingChamp,
    Group,
    PillowRenderer,
    RectangleMask,
    Scene,
    Text,
    Typewriter,
)


def panel(code="x = 1\n    y = 2", **kwargs):
    return CodingChamp(code, width=460, height=230, font_size=22, position=(250, 140), **kwargs)


@pytest.mark.parametrize(
    "language,code",
    [
        ("python", '\nclass Player:\n\tname = "Alex"\n'),
        ("javascript", 'const x = "hello";\n// comment'),
        ("python", "x = 1\r\n\tprint(x)\r\n"),
        ("typescript", "let x: number = 10;\n"),
    ],
)
def test_highlighting_preserves_every_source_character(language, code):
    pytest.importorskip("pygments")
    p = panel(code, language=language)
    assert "".join(t[1] for t in p.tokens) == code
    assert len({t[2] for t in p.tokens}) > 1
    assert p.code == code
    assert p.visible_count(1) == len(code)


def test_indentation_tabs_and_whitespace_are_fixed_during_reveal():
    p = panel("a\n\tb", tab_size=4)
    assert p.visible_count(0) == 0
    assert p.visible_count(0.5) == 2
    assert p.visible_count(1) == 4
    first = p._rows[0][0]
    second = p._rows[1][-1]
    assert second[1] > first[1]
    assert p.bounds.width == 460


def test_word_and_authored_block_boundaries():
    p = panel("  hello  world\n  again", reveal_mode="word")
    assert p.visible_count(0.32) == 0
    assert p.code[: p.visible_count(1 / 3)] == "  hello  "
    assert p.code[: p.visible_count(2 / 3)] == "  hello  world\n  "
    p = panel("one\ntwo\nthree", reveal_mode="block", block_ends=(2, 3))
    assert p.visible_count(0.499) == 0
    assert p.code[: p.visible_count(0.5)] == "one\ntwo\n"
    assert p.visible_count(1) == len(p.code)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reveal_mode": "bad"},
        {"block_ends": (1,)},
        {"block_ends": (2, 1)},
        {"highlighted_lines": (4,)},
        {"tab_size": 0},
        {"first_line": True},
        {"font_size": float("nan")},
        {"width": 10},
        {"height": 10},
        {"theme": "unknown"},
    ],
)
def test_invalid_configuration_fails_before_render(kwargs):
    options = {"width": 460, "height": 230, "font_size": 22}
    options.update(kwargs)
    with pytest.raises(ValueError):
        CodingChamp("x\ny", **options)


def test_long_code_reports_actionable_overflow():
    with pytest.raises(ValueError, match="shorter excerpt"):
        panel("x" * 200)
    with pytest.raises(ValueError, match="shorter excerpt"):
        panel("x\n" * 100)


def test_missing_highlighter_does_not_break_plain_text(monkeypatch):
    real_import = builtins.__import__

    def without_pygments(name, *args, **kwargs):
        if name.startswith("pygments"):
            raise ImportError("disabled for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_pygments)
    assert panel().code
    with pytest.raises(ImportError, match=r"faceless-champ\[coding\]"):
        panel(language="python")


def test_unknown_language_has_explicit_error():
    pytest.importorskip("pygments")
    with pytest.raises(ValueError, match="Unknown coding language"):
        panel(language="no-such-language-codingchamp")


@pytest.mark.parametrize("theme", ["midnight", "ocean", "paper"])
def test_themes_are_customizable_immutable_and_snapshot_safe(theme):
    t = CodeTheme.named(theme)
    custom = replace(t, accent="#123456", syntax={"Keyword": "#654321"})
    assert custom.token_color("Token.Keyword.Constant") == "#654321"
    assert custom.token_color("Token.Name") == custom.foreground
    assert deepcopy(custom) is custom
    with pytest.raises(TypeError):
        custom.syntax["Name"] = "red"
    scene = Scene(Canvas(500, 280))
    scene.play(CodeReveal(panel(theme=custom)))
    PillowRenderer(1).validate(scene)


def test_staged_reveals_keep_fixed_geometry_and_random_access_cache_parity():
    p = panel()
    scene = Scene(Canvas(500, 280))
    scene.play(CodeReveal(p, end=0.5), run_time=1)
    scene.wait(1)
    scene.play(CodeReveal(p, start=0.5), run_time=1)
    scene.wait(0.1)
    entry = scene.entries[0]
    assert entry.state_at(1.5)["reveal"] == 0.5
    assert entry.state_at(3)["reveal"] == 1
    cached = PillowRenderer(1)
    uncached = PillowRenderer(1, frame_cache_mb=0, code_cache_mb=0)
    for t in (0, 0.4, 1, 2.5, 3, 0.4):
        assert scene.bounds_at(p, t) == p.bounds
        assert cached.frame(scene, t, (500, 280)).tobytes() == uncached.frame(scene, t, (500, 280)).tobytes()
    assert len(cached._code_sprites) == 1
    assert cached._code_cache_bytes <= cached._code_cache_limit
    assert not uncached._code_sprites
    # Existing Text typewriter is still restricted to Text.
    assert Typewriter(Text("old")).targets == {"reveal": 1.0}
    with pytest.raises(TypeError):
        Typewriter(p)


def test_editor_transforms_masks_and_bounded_eviction():
    scene = Scene(Canvas(500, 280))
    p = panel(mask=RectangleMask(width=200, height=180))
    group = Group(p)
    scene.play(group.animate.scale_to(0.8), run_time=1)
    scene.wait(0.1)
    renderer = PillowRenderer(1, code_cache_mb=1)
    renderer.frame(scene, 0.5, (500, 280))
    for i in range(4):
        c = panel(str(i))
        renderer._sprite(c, c.state(), 1, 0)
    assert renderer._code_cache_bytes <= 1024 * 1024
    assert len(renderer._code_sprites) == 1


@pytest.mark.parametrize("start,end", [(-1, 1), (0, 2), (0.8, 0.2), (0, float("nan"))])
def test_reveal_validation(start, end):
    with pytest.raises(ValueError):
        CodeReveal(panel(), start=start, end=end)
