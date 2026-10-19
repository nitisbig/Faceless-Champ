"""Particle ink includes the overhang while layout retains the field size."""

import pytest

from faceless_champ import Canvas, EffectStack, Group, ParticleField, PillowRenderer, Scene


@pytest.mark.parametrize("isolation", ["leaf", "group", "nested_group"])
def test_cpu_particle_overhang_survives_noop_isolation(isolation):
    pytest.importorskip("numpy")

    def scene(isolated):
        field = ParticleField(width=20, height=20, radius=25, count=10, position=(80, 80))
        if isolation == "leaf":
            field.effects = EffectStack() if isolated else None
            root = field
        else:
            root = Group(field, effects=EffectStack() if isolated else None)
            if isolation == "nested_group":
                root = Group(root, effects=EffectStack() if isolated else None)
        return Scene(Canvas(160, 160, "#00000000")).add(root).wait(1)

    with PillowRenderer(1) as renderer:
        direct = renderer.frame(scene(False), 0.3, (160, 160))
        isolated = renderer.frame(scene(True), 0.3, (160, 160))
    l, t, r, b = direct.getbbox()
    assert l < 60 and t < 60 and r > 100 and b > 100
    assert isolated.tobytes() == direct.tobytes()


def test_particle_ink_bounds_include_radius_and_aa_without_expanding_layout():
    field = ParticleField(width=20, height=20, radius=25, position=(80, 80), anchor="top_left")
    scene = Scene(Canvas(200, 200)).add(field).wait(1)
    logical = scene.bounds_at(field, 0)
    ink = scene.ink_bounds_at(field, 0)
    assert logical.width == logical.height == 20
    assert ink.left == logical.left - 26
    assert ink.top == logical.top - 26
    assert ink.right == logical.right + 26
    assert ink.bottom == logical.bottom + 26
