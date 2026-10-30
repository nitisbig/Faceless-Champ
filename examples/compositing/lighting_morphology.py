"""Skia Lighting and Morphology showcase (12 seconds).

An embossed title under a swinging distant light, point- and spot-lit shapes
whose light travels across them, then text that dilates and erodes.

    python examples/compositing/lighting_morphology.py --frame 1 5 10 --backend skia
    python examples/compositing/lighting_morphology.py --quality medium --backend skia
"""

from faceless_champ import (
    Circle,
    EffectStack,
    FadeOut,
    Lighting,
    Morphology,
    Rectangle,
    Scene,
    Text,
    Theme,
    run,
)

theme = Theme.named("midnight")


def build():
    with theme.use():
        scene = Scene(theme.canvas())
        area = scene.canvas.safe_area()
        cx, cy = area.center

        # Beat 1: an embossed title while a distant light circles it.
        title = Text(
            "LIGHTING",
            role="display",
            color=theme.color("primary"),
            position=(cx, area.top + area.height * 0.18),
            effects=EffectStack(lighting=Lighting(azimuth=135, elevation=35, bevel=8, depth=6, specular=0.7)),
        )
        scene.reveal(title)
        scene.wait(0.5)
        scene.play(title.animate.effect_to("lighting", azimuth=495), run_time=3, rate_func="emphasized")

        # Beat 2: a point light sweeps a sphere, a spotlight scans a raised card.
        row = area.top + area.height * 0.6
        sphere = Circle(
            170,
            fill=theme.color("secondary"),
            stroke=None,
            position=(cx - area.width * 0.22, row),
            effects=EffectStack(
                lighting=Lighting(light="point", x=-0.1, y=0.1, height=260, bevel=40, depth=30, specular=0.9)
            ),
        )
        card = Rectangle(
            width=area.width * 0.32,
            height=300,
            corner_radius=36,
            fill=theme.color("highlight"),
            stroke=None,
            position=(cx + area.width * 0.2, row),
            effects=EffectStack(
                lighting=Lighting(light="spot", x=0.15, y=0.5, height=420, cone=75, bevel=14, depth=8, specular=0.6)
            ),
        )
        scene.reveal(sphere, card, stagger=0.2)
        scene.wait(0.7)
        scene.play(
            sphere.animate.effect_to("lighting", x=1.0, y=0.4),
            card.animate.effect_to("lighting", x=0.85),
            run_time=3,
            rate_func="emphasized",
        )
        scene.play(FadeOut(sphere), FadeOut(card), run_time=0.5)

        # Beat 3: morphology grows one word and thins another.
        grow = Text(
            "Dilate",
            role="display",
            position=(cx - area.width * 0.2, row),
            effects=EffectStack(morphology=Morphology(radius=0)),
        )
        thin = Text(
            "Erode",
            role="display",
            position=(cx + area.width * 0.2, row),
            effects=EffectStack(morphology=Morphology(radius=0, mode="erode")),
        )
        scene.reveal(grow, thin, stagger=0.15)
        scene.wait(0.6)
        scene.play(
            grow.animate.effect_to("morphology", radius=4),
            thin.animate.effect_to("morphology", radius=3),
            run_time=2,
            rate_func="emphasized",
        )
        scene.wait(max(0.0, 12 - scene.duration))
        return scene


scene = build()
if __name__ == "__main__":
    run(build)
