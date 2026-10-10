"""Thirty-second tour. All browser and visual behavior comes from public APIs."""

from pathlib import Path

from facelesschamp_kit.blocks import WebElement, WebWalkthrough
from facelesschamp_kit.context import BuildContext

from faceless_champ import Bounds, Canvas, FadeIn, Scene, Text
from faceless_champ.web import HtmlPage, WebCallout, WebFocus, WebHighlight, WebScript

ROOT = Path(__file__).resolve().parent
CANVAS = Canvas(1920, 1080, "#101827")
STORYBOARD_TIMES = [2, 7, 11, 16, 21, 25, 28]


def browser_script():
    page = HtmlPage(ROOT / "chatgpt-ui.html", viewport=(1440, 900), ready=("#prompt-input",))
    script = WebScript(30)
    script.track("#thread-compose .composer", ".composer", ".message.assistant pre", "#theme-choice", "#sidebar")
    script.move("#prompt-input", at=4, duration=0.6)
    script.click("#prompt-input", at=4.6)
    script.type("#prompt-input", "Explain async JavaScript", at=5, duration=2.5)
    script.move("#send", at=7.6, duration=0.4)
    script.click("#send", at=8.1)
    script.scroll("#thread-scroller", at=13, y=180, duration=1)
    script.move("#profile", at=18, duration=0.6)
    script.click("#profile", at=18.6)
    script.select("#theme-choice", "dark", at=20)
    script.press("#theme-choice", "Escape", at=22)
    return page, script


def build_video(capture):
    ctx = BuildContext(ROOT, canvas=CANVAS, safe_margin=72, caption_space=0)
    scene = Scene(CANVAS)
    walkthrough = WebWalkthrough(
        capture,
        title="ChatGPT-inspired interface · local HTML demo",
        highlights=(WebHighlight(".composer", 1, 4), WebHighlight("#theme-choice", 19, 22)),
        focuses=(WebFocus(".composer", 4, 8, zoom=1.45), WebFocus(".message.assistant pre", 14, 18, zoom=1.45)),
        callouts=(
            WebCallout("Start with a question", 1, 4),
            WebCallout("Type. Send. Explore.", 5, 8),
            WebCallout("A simulated reply from the supplied HTML", 10, 13),
            WebCallout("Focus on the details", 14, 18),
            WebCallout("Make it your own", 19, 22),
        ),
    ).compose(ctx, ctx.bounds)
    scene.play(FadeIn(walkthrough.root), run_time=0.7)
    with scene.at(24):
        scene.remove(walkthrough.root)
        element = WebElement(capture, "#thread-compose .composer", source_start=24).compose(
            ctx, Bounds(200, 390, 1720, 760)
        )
        heading = Text("Every UI element can become a scene", font_size=58, position=(960, 250), color="white")
        scene.add(element.root, heading)
    with scene.at(27):
        scene.remove(element.root, heading)
        final = WebWalkthrough(
            capture,
            source_start=27,
            title="Built from one HTML file",
            cursor=False,
            callouts=(WebCallout("Your interface. Your story.", 27, 30),),
        ).compose(ctx, ctx.bounds)
        scene.add(final.root)
    scene.wait_until(30)
    return scene
