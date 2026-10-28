import pytest

from faceless_champ import Bounds, Text, TextBudgetError, TypeScale, fit_text, font_path


def test_wrap_paragraphs_and_fit_bounds():
    box = Bounds(20, 30, 240, 210)
    text = fit_text(
        "Systems connect inputs and outputs\nUseful ideas", box, font_size=44, min_font_size=24, color="black"
    )
    assert isinstance(text, Text)
    assert "\n" in text.text
    assert text.text.endswith("Useful ideas")
    assert text.position == box.center
    assert text.bounds.width <= box.width
    assert text.bounds.height <= box.height


def test_minimum_size_is_tried_and_long_words_fail():
    box = Bounds(0, 0, 300, 100)
    text = fit_text("Hello", box, font_size=25.5, min_font_size=25)
    assert 25 <= text.font_size <= 25.5
    with pytest.raises(ValueError, match="cannot fit"):
        fit_text("unbreakableword" * 10, box, font_size=25, min_font_size=25)


@pytest.mark.parametrize("kwargs", [{"font_size": float("nan")}, {"min_font_size": 70}, {"spacing": -1}])
def test_bad_styles(kwargs):
    with pytest.raises(ValueError):
        fit_text("Hello", Bounds(0, 0, 300, 100), **kwargs)


def test_blank_or_empty_box():
    with pytest.raises(ValueError):
        fit_text("  ", Bounds(0, 0, 100, 100))
    with pytest.raises(ValueError):
        fit_text("Hello", Bounds(0, 0, 0, 100))


def test_default_shrink_is_one_step_and_reports_budget():
    box = Bounds(20, 30, 240, 210)
    with pytest.raises(TextBudgetError, match="cannot fit"):
        fit_text("Systems connect inputs and outputs\nUseful ideas", box, font_size=44)
    fitted = fit_text("Short label", Bounds(0, 0, 600, 120), font_size=44)
    assert fitted.font_size >= 44 * 0.85


def test_role_budgets_reject_paragraphs_and_can_be_disabled():
    wide = Bounds(0, 0, 1800, 900)
    with pytest.raises(TextBudgetError, match="words exceed the title budget"):
        fit_text("one two three four five six seven eight nine", wide, role="title")
    text = fit_text("one two three four five six seven eight nine", wide, role="title", budget=False)
    assert text.role is None and text.font_size == 84
    with pytest.raises(TextBudgetError, match="lines"):
        fit_text("A clear and readable body sentence " * 3, Bounds(0, 0, 420, 900), role="body")


def test_role_styles_and_explicit_overrides():
    title = Text("Revenue doubled", role="title")
    assert (title.font_size, title.font_weight, title.line_height, title.tracking) == (84, 700, 1.06, -0.01)
    assert Text("x", role="title", font_size=40).font_size == 40
    serif = Text("Quote", role="heading", type_scale=TypeScale.named("editorial"))
    assert serif.font == font_path("serif")
    assert Text("Plain").font == font_path("sans")
    with pytest.raises(ValueError, match="Unknown text role"):
        Text("x", role="huge")
    with pytest.raises(ValueError, match="Unknown font"):
        Text("x", font="comic")


def test_balanced_wrap_avoids_single_word_last_line():
    text = fit_text("Gradients flow backward through every layer", Bounds(0, 0, 900, 400), role="heading")
    lines = text.text.split("\n")
    assert len(lines) == 2 and len(lines[-1].split()) >= 2


def test_missing_glyphs_fall_back_with_warning():
    with pytest.warns(UserWarning, match="fallback"):
        arrow = Text("Input \u2192 \u03bb output", font="sans", font_weight=700)
    assert arrow.font == font_path("fallback") and arrow.font_weight is None
    assert Text("Plain ascii", font_weight=700).font_weight == 700


def test_line_height_and_tracking_change_measured_size():
    base = Text("Two\nlines", font_size=60)
    tall = Text("Two\nlines", font_size=60, line_height=1.6)
    tight = Text("Tracking", font_size=60, tracking=-0.05)
    loose = Text("Tracking", font_size=60, tracking=0.1)
    assert tall.bounds.height > base.bounds.height
    assert loose.bounds.width > tight.bounds.width
