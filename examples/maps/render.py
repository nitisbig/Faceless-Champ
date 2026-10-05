"""Offline map showcase: uv run --extra maps python examples/maps/render.py --preview."""

import argparse
from pathlib import Path

from faceless_champ import Canvas, EarthMap, OutlineMap, PillowRenderer, SatelliteMap, Scene, Sequence


def showcase():
    canvas = Canvas(1280, 720)
    scenes = []
    for country in (None, "Nepal"):
        scene = Scene(canvas)
        scene.add(
            OutlineMap(
                country,
                width=1120,
                height=600,
                position=(640, 360),
                fill="#153c55",
                border_color="#78dbff",
                border_width=2,
            )
        )
        scene.wait(2)
        scenes.append(scene)
    scene = Scene(canvas)
    satellite = SatelliteMap(width=1160, height=600, position=(640, 360))
    scene.add(satellite)
    scene.wait(0.5)
    scene.play(satellite.animate.zoom_to("Nepal"), run_time=2)
    scene.wait(0.5)
    scene.play(satellite.animate.zoom_to("Pacific Ocean", zoom=2), run_time=2)
    scene.play(satellite.animate.rotate(30), run_time=1)
    scenes.append(scene)
    scene = Scene(canvas)
    earth = EarthMap(width=650, height=650, position=(640, 360), longitude=20, latitude=15)
    scene.add(earth)
    scene.play(earth.animate.rotate(longitude=360), run_time=3)
    scene.play(earth.animate.zoom_to("Nepal"), run_time=2)
    scene.wait(0.5)
    scene.play(earth.animate.zoom_to("Pacific Ocean", zoom=1.3), run_time=2)
    scene.wait(0.5)
    scenes.append(scene)
    return Sequence(*scenes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--quality", choices=["preview", "hd", "full-hd", "4k"], default="hd")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("media/maps"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    quality = "preview" if args.preview else args.quality
    width, height = {"preview": (640, 360), "hd": (1280, 720), "full-hd": (1920, 1080), "4k": (3840, 2160)}[quality]
    fps = args.fps if args.fps is not None else (12 if quality == "preview" else 24)
    if fps <= 0:
        parser.error("--fps must be positive")
    movie = showcase()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stills:
        renderer = PillowRenderer()
        renderer.validate(movie)
        for name, time in [
            ("outline-world", 0),
            ("outline-nepal", 2),
            ("satellite-world", 4),
            ("satellite-nepal", 6.5),
            ("satellite-pacific", 9),
            ("earth-start", 10),
            ("earth-turn", 11.5),
            ("earth-nepal", 15),
            ("earth-final", 17.99),
        ]:
            path = args.output / f"{name}.png"
            if path.exists() and not args.overwrite:
                raise FileExistsError(f"{path} exists; pass --overwrite")
            renderer.frame(movie, time, (width, height)).save(path)
        print(f"Saved stills in {args.output}")
    else:
        path = args.output / "maps.mp4"

        def progress(done, total):
            if done == 0 or done == total or done % max(1, fps) == 0:
                print(f"Rendering maps: {done}/{total} frames", flush=True)

        movie.render(
            path, width=width, height=height, fps=fps, preset="fast", overwrite=args.overwrite, progress=progress
        )
        print(path)


if __name__ == "__main__":
    main()
