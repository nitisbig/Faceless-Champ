"""PyVista offscreen renders of lit glass solids, camera-matched to space.Camera.

The folder is ``pv3d`` (not ``pyvista``) so it never shadows the installed package.

    rgba = render(meshes, cam, size)       # HxWx4 uint8, straight alpha, transparent background
    composite(fr, rgba)                    # draw it under the skia edges of the same frame

Edges are never drawn in VTK: skia draws them from the same coordinates, so lines stay razor-sharp.
Frames are cached on disk by (meshes, camera, size), so a solid is rendered once per frame forever.
"""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from fx import LINEAR
from theme import TOKENS, H, W

CACHE = Path(__file__).resolve().parents[1] / "output" / "cache" / "pyvista"

# Phong, not PBR: without an environment map PBR reads flat on black; Phong gives a sculpted, crisp highlight.
GLASS = dict(color=TOKENS["w"], opacity=0.30, specular=1.0, specular_power=100, diffuse=0.5, ambient=0.35,
             smooth_shading=False)  # flat facets: a cut-crystal look for the slice solids
GLOSS = dict(color="#2A3346", specular=1.0, specular_power=90, diffuse=0.9, ambient=0.04, smooth_shading=True)


@lru_cache(maxsize=2)
def _plotter(width: int, height: int):
    import pyvista as pv

    p = pv.Plotter(off_screen=True, window_size=(width, height), lighting="none")
    p.set_background("black")
    p.enable_depth_peeling(number_of_peels=8)
    p.enable_anti_aliasing("ssaa")
    return p


# space.Camera uses right = up x forward, i.e. a left-handed world. VTK is right-handed, so the VTK scene
# is the skia world mirrored in x; the rendered image then matches cam.project exactly.
MIRROR = np.array([-1.0, 1.0, 1.0])


def _lights(p, cam):
    """One warm key light from above-left and one blue rim light from behind (scene lights, fixed in world)."""
    import pyvista as pv

    p.remove_all_lights()
    target = cam.target

    def at(offset):
        return tuple((target + np.asarray(offset, float)) * MIRROR)

    key = pv.Light(position=at([-4.0, 7.0, -5.0]), focal_point=at([0, 0, 0]), color=TOKENS["light"], intensity=1.7,
                   light_type="scene light")
    rim = pv.Light(position=at([3.5, 2.0, 7.0]), focal_point=at([0, 0, 0]), color=TOKENS["w"], intensity=1.3,
                   light_type="scene light")
    fill = pv.Light(position=tuple(cam.eye * MIRROR), focal_point=at([0, 0, 0]), color="#ffffff", intensity=0.35,
                    light_type="scene light")
    for light in (key, rim, fill):
        p.add_light(light)


def match_camera(p, cam, width: int, height: int):
    """Same eye, target, up and field of view as ``space.Camera`` (focal is in 1920x1080 design px)."""
    p.camera.position = tuple(cam.eye * MIRROR)
    p.camera.focal_point = tuple(cam.target * MIRROR)
    p.camera.up = (0.0, 1.0, 0.0)
    p.camera.view_angle = math.degrees(2 * math.atan((H / 2) / cam.focal))
    # An off-centre principal point (cam.cx, cam.cy) is a window-centre shift in normalised device units;
    # VTK moves the window, so the image content moves the opposite way.
    p.camera.SetWindowCenter(-(cam.cx - W / 2) / (W / 2), (cam.cy - H / 2) / (H / 2))
    p.camera.clipping_range = (0.05, 200.0)


def _key(meshes, cam, size) -> str:
    h = hashlib.sha1()
    for mesh, style in meshes:
        h.update(np.ascontiguousarray(mesh.points, np.float32).tobytes())
        h.update(np.ascontiguousarray(mesh.faces if hasattr(mesh, "faces") else [], np.int64).tobytes())
        h.update(repr(sorted(style.items())).encode())
    h.update(np.round(np.r_[cam.eye, cam.target, cam.focal, cam.cx, cam.cy], 5).tobytes())
    h.update(repr(size).encode())
    return h.hexdigest()[:20]


def render(meshes, cam, size, cache: str | None = "default") -> np.ndarray:
    """``meshes``: [(pyvista mesh, add_mesh kwargs)]. Returns HxWx4 uint8 RGBA (straight alpha)."""
    width, height = int(size[0]), int(size[1])
    path = None
    if cache:
        path = CACHE / cache / f"{_key(meshes, cam, (width, height))}.png"
        if path.exists():
            from PIL import Image

            return np.asarray(Image.open(path).convert("RGBA"))
    p = _plotter(width, height)
    p.clear_actors()
    for mesh, style in meshes:
        mirrored = mesh.copy()
        mirrored.points = np.asarray(mesh.points) * MIRROR
        # The mirror reverses face winding: reverse it back, so any normals VTK derives (smooth_shading recomputes
        # them) point outward again. Works for open surfaces too, e.g. a sphere clipped by the Flatland sheet.
        mirrored.point_data.pop("Normals", None)
        mirrored = mirrored.extract_surface(algorithm="dataset_surface")
        mirrored.flip_faces(inplace=True)
        p.add_mesh(mirrored, **style)
    _lights(p, cam)
    match_camera(p, cam, width, height)
    p.render()  # without this the screenshot returns the previous frame's pixels
    rgba = np.asarray(p.screenshot(transparent_background=True, return_img=True), np.uint8)
    if rgba.shape[2] == 3:
        rgba = np.dstack([rgba, np.full(rgba.shape[:2], 255, np.uint8)])
    if path is not None:
        from PIL import Image

        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba, "RGBA").save(path, compress_level=1)  # ~10x smaller than raw .npy frames
    return rgba


def composite(fr, rgba: np.ndarray, alpha: float = 1.0):
    """Draw a full-frame PyVista render into an fx.Frame (any output size; it is stretched to the frame)."""
    if alpha <= 0.003:
        return
    img = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType,
                               alphaType=skia.kUnpremul_AlphaType)
    fr.c.drawImageRect(img, skia.Rect.MakeWH(W, H), LINEAR, skia.Paint(AntiAlias=True, Alphaf=alpha))


def frame_size(fr) -> tuple[int, int]:
    """Render at the output resolution of the frame being drawn."""
    return fr.w, fr.h
