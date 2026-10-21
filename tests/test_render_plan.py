"""Compilation ownership, arbitrary-time evaluation and transactional invalidation."""

from dataclasses import FrozenInstanceError

import pytest

from faceless_champ import Animation, Canvas, Group, Rectangle, Scene, Sequence, Stagger, linear
from faceless_champ._rendering.evaluate import composition_plan, evaluate_frame
from faceless_champ._rendering.plan import compile_renderable, compile_scene


@pytest.mark.parametrize("count", [5, 9, 17, 33, 129])
@pytest.mark.parametrize("wide", [False, True])
def test_one_owned_snapshot_per_node(count, wide):
    leaves = [Rectangle(width=10, height=10) for _ in range(count)]
    root = Group(*leaves) if wide else leaves[0]
    if not wide:
        for _ in range(count - 1):
            root = Group(root)
    scene = Scene().add(root)
    plan = compile_scene(scene)
    snapshots = {id(e.component) for e in scene.entries}
    retained = set()

    def visit(c):
        retained.add(id(c))
        if isinstance(c, Group):
            for child in c.children:
                visit(child)

    for node in plan.nodes:
        visit(node.component)
        assert node.component is scene.entries[node.id].component
        assert tuple(id(child) for child in getattr(node.component, "children", ())) == tuple(
            id(scene.entries[index].component) for index in node.child_ids
        )
    assert retained == snapshots
    assert len(retained) == (count + 1 if wide else count)
    leaves[0].fill = "red"
    assert all(node.component is not leaves[0] for node in plan.nodes)
    assert scene.entries[-1].component.fill != "red"


def test_compilation_is_cached_owned_and_invalidated_by_supported_operations():
    c = Rectangle(width=10, height=10)
    scene = Scene(Canvas(100, 100)).add(c)
    before = compile_scene(scene)
    assert compile_scene(scene) is before
    with pytest.raises((FrozenInstanceError, AttributeError)):
        before.nodes = ()
    with pytest.raises(TypeError):
        before.nodes[0].initial["opacity"] = 0
    scene.play(c.animate.move_to(20, 30), run_time=1, rate_func=linear)
    after = compile_scene(scene)
    assert after is not before and not before.nodes[0].tracks
    assert after.nodes[0].component is before.nodes[0].component
    scene.play(Stagger(c.animate.move_to(40, 50)), run_time=1)
    scheduled = compile_scene(scene)
    assert scheduled is not after
    scene.wait(1)
    waited = compile_scene(scene)
    assert waited is not scheduled and waited.duration == 3
    scene.remove(c)
    assert compile_scene(scene).nodes[0].end == 3


def test_absolute_cursor_invalidates_during_context_as_well_as_on_exit():
    scene = Scene().wait(1)
    before = compile_scene(scene)
    with scene.at(5):
        during = compile_scene(scene)
        assert during is not before and during.duration == 5
    assert compile_scene(scene) is not during and scene.duration == 5


@pytest.mark.parametrize("kind", ["scene", "sequence", "grid", "layer"])
def test_rendered_compositions_can_be_copied_and_pickled_without_execution_caches(kind):
    import pickle
    from copy import deepcopy

    from faceless_champ import Grid, Layer, PillowRenderer

    c = Rectangle(width=20, height=10, fill="red", position=(25, 25))
    scene = Scene(Canvas(50, 50)).play(c.animate.move_to(30, 30), run_time=1)
    node = {
        "scene": lambda: scene,
        "sequence": lambda: Sequence(scene),
        "grid": lambda: Grid(scene, rows=1, columns=1, canvas=scene.canvas),
        "layer": lambda: Layer(scene),
    }[kind]()
    with PillowRenderer(1) as renderer:
        expected = renderer.frame(node, 0.4, (50, 50)).tobytes()
        for clone in (deepcopy(node), pickle.loads(pickle.dumps(node))):
            assert clone._compiled_plan is None
            assert renderer.frame(clone, 0.4, (50, 50)).tobytes() == expected


def test_arbitrary_order_states_geometry_lifetimes_and_stable_z_ties():
    a = Rectangle(width=20, height=10, position=(30, 30))
    b = Rectangle(width=10, height=10, position=(50, 30))
    root = Group(a, b, rotation=17, scale_x=1.3)
    scene = Scene().add(root)
    scene.play(a.animate.move_to(60, 40), root.animate.rotate_to(55), run_time=2, rate_func=linear)
    scene.play(a.animate.move_to(80, 30), run_time=1, rate_func=linear).remove(b).wait(1)
    spec = compile_scene(scene)
    assert spec.nodes[0].child_ids == (1, 2)
    for time in (3.5, 0, 2.4, 1, 4, 0, 3):
        frame = evaluate_frame(scene, time)
        assert [dict(e.state) for e in frame.entries] == [e.state_at(time) for e in scene.entries]
        for authored, entry, geometry in zip((root, a, b), frame.entries, frame.geometry):
            assert geometry.logical == scene.bounds_at(authored, time)
            assert geometry.age == max(0, time - entry.start)
        assert frame.geometry[2].visible == (time < 3)


def test_failed_conflicts_and_failed_resolution_leave_cached_plan_unchanged():
    c = Rectangle(width=20, height=10)
    scene = Scene().add(c)
    plan = compile_scene(scene)
    with pytest.raises(ValueError, match="Overlapping"):
        scene.play(c.animate.move_to(1, 2), c.animate.move_to(3, 4))
    assert compile_scene(scene) is plan and scene.time == 0

    class Failed(Animation):
        def resolve(self, state):
            state["position"] = (99, 99)
            raise ValueError("bad resolution")

    with pytest.raises(ValueError, match="bad resolution"):
        scene.play(Failed(c, {"position": (3, 4)}))
    assert compile_scene(scene) is plan and c.position == (0, 0)


def test_component_hook_and_detached_animation_extension():
    class Custom(Rectangle):
        def state(self):
            return {**super().state(), "temperature": 20}

        def validate_animation(self, property, value):
            if property == "temperature":
                if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                    raise ValueError("temperature range")
            else:
                super().validate_animation(property, value)

    c = Custom(width=20, height=10)
    animation = Animation(c, {"temperature": 80})
    detached = animation.resolve(c.state())
    detached.targets["temperature"] = 90
    assert animation.targets["temperature"] == 80
    scene = Scene().play(animation, run_time=2, rate_func=linear)
    assert evaluate_frame(scene, 1, geometry=False).entries[0].state["temperature"] == 50
    plan = compile_scene(scene)
    with pytest.raises(ValueError, match="temperature range"):
        scene.play(Animation(c, {"temperature": 101}))
    assert compile_scene(scene) is plan


def test_composition_specs_keep_terminal_left_limit_and_recompile_children():
    c = Rectangle(width=10, height=10)
    first = Scene().add(c).wait(1).remove(c)
    second = Scene().wait(1)
    sequence = Sequence(first, second)
    before = compile_renderable(sequence)
    assert compile_renderable(sequence) is before
    parts, _ = composition_plan(before, 2, (100, 100))
    assert parts[0].time < 1
    first.wait(1)
    after = compile_renderable(sequence)
    assert after is not before and before.duration == 2 and after.duration == 3


def test_existing_two_method_renderer_receives_public_scene_and_is_caller_owned(tmp_path):
    from PIL import Image

    from faceless_champ import save_frame

    scene = Scene(Canvas(10, 10)).wait(1)
    calls = []

    class CustomRenderer:
        def validate(self, node):
            assert node is scene
            calls.append("validate")

        def frame(self, node, time, size):
            assert node is scene and time == 0.4 and size == (10, 10)
            calls.append("frame")
            return Image.new("RGBA", size, "red")

    result = save_frame(scene, 0.4, tmp_path / "frame.png", size=(10, 10), renderer=CustomRenderer())
    assert result.is_file() and calls == ["validate", "frame"]
