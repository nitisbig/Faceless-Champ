import pytest

from faceless_champ import Bounds, Text, fit_text


def test_wrap_paragraphs_and_fit_bounds():
    box = Bounds(20, 30, 240, 210)
    text = fit_text("Systems connect inputs and outputs\nUseful ideas", box, font_size=44, color="black")
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
