"""Stage A engine smoke tests (run once per machine; outputs land in output/frames/smoke/).

    python smoke_tests.py --pyvista     # glass solids camera-matched under skia edges + alignment check
    python smoke_tests.py --manim       # prepare a Manim clip and composite one frame over a skia frame
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "output" / "frames" / "smoke"
SIZE = (1280, 720)


def save(arr, name):
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr[..., :3]).save(OUT / name)
    print("wrote", OUT / name)


def pyvista_test():
    from components import tesseract as T4
    from fx import Frame
    from pv3d import render as pvr
    from pv3d import solids
    from space import orbit, rot_y

    # 1) alignment: an unlit opaque box must land exactly on its skia-projected corners
    half, R = (1.0, 0.8, 1.2), rot_y(0.4)
    corners = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) * half @ R.T
    k = SIZE[0] / 1920
    worst = 0.0
    for center in ((960.0, 540.0), (1100.0, 500.0), (700.0, 640.0)):
        cam = orbit((0, 0, 0), 6.0, 0.35, -0.6, focal=1500.0, center=center)
        rgba = pvr.render([(solids.box(half=half, R=R), dict(color="white", lighting=False))], cam, SIZE, cache=None)
        ys, xs = np.nonzero(rgba[..., 3] > 128)
        px, py, _ = cam.project(corners)
        err = max(abs(xs.min() - px.min() * k), abs(xs.max() - px.max() * k), abs(ys.min() - py.min() * k),
                  abs(ys.max() - py.max() * k))
        worst = max(worst, err)
    print(f"alignment: worst bbox error {worst:.2f} px at 720p  ({'OK' if worst <= 1.5 else 'FAIL'})")

    # 2) look: glass sphere (S14/S15) and the octahedron slice (S16) with skia edges on top
    t0 = time.time()
    fr = Frame(SIZE)
    cam = orbit((0, 0, 0), 7.0, 0.30, -0.5, focal=1500.0, center=(560.0, 540.0))
    sphere = pvr.render([(solids.sphere(radius=1.4), pvr.GLOSS | dict(color="#20262F"))], cam, SIZE, cache="smoke")
    pvr.composite(fr, sphere)
    pts, loops = T4.corner_slice(2.0)
    world = T4.place(pts, scale=1.5)
    cam2 = orbit((0, 0, 0), 6.0, 0.32, 0.55, focal=1500.0, center=(1380.0, 520.0))
    solid = pvr.render([(solids.convex_solid(world, loops), pvr.GLASS | dict(color=_hex("w")))], cam2, SIZE,
                       cache="smoke")
    pvr.composite(fr, solid)
    T4.draw_solid(fr, cam2, world, loops, "w", 1.0, fill=0.0, sweep=0.45)
    fr.text("PyVista glass + skia edges", 960, 1000, "sans", 30, 600, "muted")
    save(fr.finish(), "pyvista_glass.png")
    print(f"look frame: {time.time() - t0:.1f}s (cached renders are reused on the next run)")


def _hex(token):
    from theme import TOKENS

    return TOKENS[token]


def manim_test():
    from fx import Frame
    from theme import TOKENS

    from faceless_champ.integrations.manim import ManimRenderOptions, ManimSceneSpec, prepare_manim
    from faceless_champ.prepared import PreparedFrameSource

    t0 = time.time()
    spec = ManimSceneSpec(str(ROOT / "manim" / "smoke.py"), "Smoke",
                          inputs=("fonts/STIXGeneral.ttf", "fonts/STIXGeneralItalic.ttf"),
                          parameters={"colors": {k: TOKENS[k] for k in ("x", "y", "z", "w", "ink", "muted")}})
    options = ManimRenderOptions(width=1280, height=720, fps=30, background=None)
    prepared = prepare_manim(spec, cache_dir=ROOT / "output" / "cache" / "manim", options=options,
                             python=sys.executable)
    print(f"prepared in {time.time() - t0:.1f}s: {prepared}")
    source = prepared if isinstance(prepared, PreparedFrameSource) else PreparedFrameSource(prepared)
    print("duration", getattr(source, "duration", None))
    from theme import THEME, H, W

    from faceless_champ import FunctionSource, Scene, Viewport, save_frame

    def back(t, size):
        fr = Frame(size)
        fr.text("skia layer under a Manim overlay", 960, 980, "sans", 30, 600, "muted")
        return fr.finish()

    with THEME.use():
        scene = Scene(THEME.canvas())
        scene.add(FunctionSource(back, size=(W, H), duration=3.0, key="smoke-back").viewport(
            width=W, height=H, position=(W / 2, H / 2)))
        scene.add(Viewport(source, width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(3.0)
    OUT.mkdir(parents=True, exist_ok=True)
    for t in (0.8, 2.6):
        save_frame(scene, t, OUT / f"manim_{t:.1f}.png", size=SIZE, backend="skia", overwrite=True)
        print("wrote", OUT / f"manim_{t:.1f}.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pyvista", action="store_true")
    ap.add_argument("--manim", action="store_true")
    args = ap.parse_args()
    if not (args.pyvista or args.manim):
        args.pyvista = args.manim = True
    if args.pyvista:
        pyvista_test()
    if args.manim:
        manim_test()


if __name__ == "__main__":
    main()
