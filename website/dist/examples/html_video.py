import argparse
import tempfile
from pathlib import Path
from faceless_champ import Canvas, Scene
from faceless_champ.web import HtmlClip, HtmlPage, WebCapture, WebScript, capture_html

PAGE = """<!doctype html><meta charset="utf-8">
<style>body { background: black; color: white; font: 36px sans-serif;
margin: 80px; } button { font: inherit; padding: 20px; }</style>
<h1>A prepared local page</h1><button id="count">Count: 0</button>
<script>let count=0; document.querySelector('#count').onclick = event => {
event.target.textContent = 'Count: ' + (++count); };</script>"""

def build_scene(capture_directory):
    capture = WebCapture(capture_directory)
    scene = Scene(Canvas(1920, 1080, "#000000"))
    scene.add(HtmlClip(capture, width=1440, height=900, position=(960, 540)))
    scene.wait(capture.duration)
    return scene

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--capture", help="Existing prepared capture directory")
    parser.add_argument("--cache", default=".web-cache")
    parser.add_argument("--output", default="output/html-tour.mp4")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        with tempfile.TemporaryDirectory(prefix="fc-local-page-") as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(PAGE)
            script = WebScript(4).click("#count", at=1).click("#count", at=2)
            script.track("#count")
            capture = capture_html(HtmlPage(path, viewport=(1440, 900)), script,
                                   fps=15, cache_dir=args.cache)
        directory = capture.directory
        print("Prepared:", directory)
    elif args.capture:
        directory = args.capture
    else:
        parser.error("Use --prepare or --capture PATH")
    build_scene(directory).render(args.output, width=640, height=360, fps=15,
                                  antialias=1, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
