"""Layout metrics share CPU resources without constructing renderers/sources."""

from PIL import Image as PI

from faceless_champ import Captions, Group, Image, Number, Rectangle, Scene, SubtitleCue, SubtitleTrack, Text
from faceless_champ._rendering.evaluate import evaluate_frame
from faceless_champ._rendering.measure import Measurement


def test_layout_and_ink_never_construct_renderer_or_native_context(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("measurement opened a renderer")

    monkeypatch.setattr("faceless_champ.renderer.PillowRenderer.__init__", forbidden)
    children = [Text("metrics"), Number(12), Rectangle(width=30, height=20), Image("absent.png", width=10, height=20)]
    group = Group(*children, rotation=27)
    scene = Scene().add(group).wait(1)
    assert group.bounds.width > 0
    assert scene.bounds_at(children[0], 0).width > 0
    # The image has explicit dimensions; ink measurement does not need pixels.
    assert Measurement().entry_bounds(scene.entries[-1], 0).width == 10
    assert scene.ink_bounds_at(children[-1], 0).width > 0


def test_captions_use_component_age_and_stable_phrase_keys():
    c = Captions(SubtitleTrack([SubtitleCue(1, 0, 0.5, "One"), SubtitleCue(2, 0.5, 1, "two")]), width=200)
    scene = Scene().wait(2).add(c).wait(2)
    measurement = Measurement()
    with_layout = evaluate_frame(scene, 2.1, measurement=measurement)
    second = evaluate_frame(scene, 2.6, measurement=measurement)
    assert with_layout.geometry[0].resource_key != second.geometry[0].resource_key
    assert second.geometry[0].age == 0.6000000000000001
    assert measurement.size(c, age=1.5) == (1, 1)
    assert measurement.size(c, logical=True)[1] > 1


def test_caption_measurement_reflows_after_authoring_style_changes():
    c = Captions(SubtitleTrack([SubtitleCue(1, 0, 1, "A caption with enough words to wrap")]), width=250, font_size=32)
    measurement = Measurement()
    initial = measurement.size(c, logical=True)
    c.font_size = 20
    smaller = measurement.size(c, logical=True)
    assert smaller == Measurement().size(c, logical=True) and smaller[1] < initial[1]
    c.width, c.spacing = 450, 12
    assert measurement.size(c, logical=True) == Measurement().size(c, logical=True)


def test_gif_metadata_frame_keys_follow_original_variable_durations(tmp_path):
    path = tmp_path / "sample.gif"
    PI.new("RGBA", (4, 4), "red").save(
        path, save_all=True, append_images=[PI.new("RGBA", (4, 4), "blue")], duration=[100, 300], loop=0
    )
    c = Image(path, width=20, height=20)
    measurement = Measurement()
    assert [measurement.age_key(c, t) for t in (0.05, 0.2, 0.45, 0.2)] == [0, 1, 0, 1]
    assert measurement.size(c) == (20, 20)
    measurement.close()
    assert not measurement._image_durations
