"""A shorter composition child holds its last visible, end-exclusive frame."""

import pytest

from faceless_champ import (
    Canvas,
    Captions,
    Grid,
    Layer,
    Rectangle,
    Scene,
    Sequence,
    SubtitleCue,
    SubtitleTrack,
    create_renderer,
)


@pytest.fixture(params=["pillow", "skia", "moderngl"])
def renderer(request):
    backend = request.param
    if backend != "pillow":
        pytest.importorskip("skia" if backend == "skia" else "moderngl")
    try:
        instance = create_renderer(backend, antialias=1)
    except RuntimeError as exc:
        if backend == "moderngl":
            pytest.skip(str(exc))
        raise
    with instance:
        yield instance


@pytest.mark.parametrize("kind", ["layer", "grid", "nested-offset-grid"])
def test_terminal_removal_holds_visible_content(renderer, kind):
    short = Scene(Canvas(100, 100))
    box = Rectangle(width=40, height=40, fill="red", stroke=None, position=(50, 50))
    short.add(box).wait(1).remove(box)
    long = Scene(Canvas(100, 100, "#00000000")).wait(3)
    if kind == "layer":
        node = Layer(short, long)
    elif kind == "grid":
        node = Grid(short, long, rows=1, columns=2, canvas=Canvas(200, 100))
    else:
        short = Sequence(Scene(Canvas(100, 100)).wait(0.2), short)
        node = Grid(short, long, rows=1, columns=2, canvas=Canvas(200, 100), start_times=(0.25, 0))
    size = (node.canvas.width, node.canvas.height)
    for at in (2.5, 0.9, 1.5, 2.5):
        assert renderer.frame(node, at, size).getpixel((50, 50)) == (255, 0, 0, 255)


def test_terminal_caption_holds_and_zero_duration_child_remains_valid(renderer):
    captions = Scene(Canvas(100, 100)).add(
        Captions(SubtitleTrack([SubtitleCue(1, 0, 1, "held")]), width=90, font_size=20, position=(50, 50))
    )
    long = Scene(Canvas(100, 100, "#00000000")).wait(2)
    node = Layer(captions, Scene(Canvas(100, 100, "#00000000")), long)
    before = renderer.frame(node, 0.9, (100, 100))
    assert renderer.frame(node, 1.5, (100, 100)).tobytes() == before.tobytes()


@pytest.mark.parametrize("nested", [False, True])
def test_explicit_terminal_introduction_preserves_final_state(renderer, nested):
    short = Scene(Canvas(100, 100)).wait(1)
    short.add(Rectangle(width=40, height=40, fill="red", stroke=None, position=(50, 50)))
    if nested:
        short = Sequence(Scene(Canvas(100, 100)).wait(0.2), short)
    node = Layer(short, Scene(Canvas(100, 100, "#00000000")).wait(3))
    assert renderer.frame(node, 2.5, (100, 100)).getpixel((50, 50)) == (255, 0, 0, 255)
