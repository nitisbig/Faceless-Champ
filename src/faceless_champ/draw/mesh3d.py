"""PyVista offscreen renders of lit solids, camera-matched to ``space.Camera``.

    rgba = render(meshes, cam, size)       # HxWx4 uint8, straight alpha, transparent background
    composite(fr, rgba)                    # draw it under the skia edges of the same frame

Draw edges with skia from the same coordinates rather than in VTK, so lines stay razor-sharp.
Frames are cached on disk by (meshes, styles, camera, size). Needs ``faceless-champ[3d]``.
"""

from __future__ import annotations

import hashlib
import math
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from .frame import DESIGN, LINEAR
from .palette import Palette, default_palette

# space.Camera uses right = up x forward, i.e. a left-handed world. VTK is right-handed, so the VTK scene
# is the skia world mirrored in x; the rendered image then matches cam.project exactly.
MIRROR = np.array([-1.0, 1.0, 1.0])


def glass(color="primary", palette: Palette | None = None, **overrides) -> dict:
    """add_mesh style for a faceted translucent crystal (Phong: PBR reads flat on black without an env map)."""
    style = {
        "color": (palette or default_palette()).hex(color),
        "opacity": 0.30,
        "specular": 1.0,
        "specular_power": 100,
        "diffuse": 0.5,
        "ambient": 0.35,
        "smooth_shading": False,
    }
    return {**style, **overrides}


def gloss(color="#2A3346", palette: Palette | None = None, **overrides) -> dict:
    """add_mesh style for a dark, smooth, glossy solid."""
    style = {
        "color": (palette or default_palette()).hex(color),
        "specular": 1.0,
        "specular_power": 90,
        "diffuse": 0.9,
        "ambient": 0.04,
        "smooth_shading": True,
    }
    return {**style, **overrides}


def cache_root() -> Path:
    return Path(os.environ.get("FC_CACHE_DIR") or Path.home() / ".cache" / "faceless_champ") / "pyvista"


@lru_cache(maxsize=2)
def _plotter(width: int, height: int):
    import pyvista as pv

    p = pv.Plotter(off_screen=True, window_size=(width, height), lighting="none")
    p.set_background("black")
    p.enable_depth_peeling(number_of_peels=8)
    p.enable_anti_aliasing("ssaa")
    return p


def _lights(p, cam, palette: Palette, key: str, rim: str):
    """A warm key light from above-left, a rim light from behind and a soft fill from the camera."""
    import pyvista as pv

    p.remove_all_lights()
    target = cam.target

    def at(offset):
        return tuple((target + np.asarray(offset, float)) * MIRROR)

    lights = (
        pv.Light(
            position=at([-4.0, 7.0, -5.0]),
            focal_point=at([0, 0, 0]),
            color=palette.hex(key),
            intensity=1.7,
            light_type="scene light",
        ),
        pv.Light(
            position=at([3.5, 2.0, 7.0]),
            focal_point=at([0, 0, 0]),
            color=palette.hex(rim),
            intensity=1.3,
            light_type="scene light",
        ),
        pv.Light(
            position=tuple(cam.eye * MIRROR),
            focal_point=at([0, 0, 0]),
            color="#ffffff",
            intensity=0.35,
            light_type="scene light",
        ),
    )
    for light in lights:
        p.add_light(light)


def match_camera(p, cam, design=DESIGN):
    """Same eye, target, up and field of view as ``space.Camera`` (focal in design px)."""
    dw, dh = design
    p.camera.position = tuple(cam.eye * MIRROR)
    p.camera.focal_point = tuple(cam.target * MIRROR)
    p.camera.up = (0.0, 1.0, 0.0)
    p.camera.view_angle = math.degrees(2 * math.atan((dh / 2) / cam.focal))
    # An off-centre principal point (cam.cx, cam.cy) is a window-centre shift in normalised device units;
    # VTK moves the window, so the image content moves the opposite way.
    p.camera.SetWindowCenter(-(cam.cx - dw / 2) / (dw / 2), (cam.cy - dh / 2) / (dh / 2))
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


def render(
    meshes,
    cam,
    size,
    cache: str | None = "default",
    *,
    root: str | Path | None = None,
    palette: Palette | None = None,
    key_light="light",
    rim_light="primary",
    design=DESIGN,
) -> np.ndarray:
    """``meshes``: [(pyvista mesh, add_mesh kwargs)]. Returns HxWx4 uint8 RGBA (straight alpha).

    cache: subfolder name under ``root`` (default ``$FC_CACHE_DIR/pyvista``), or None to skip the
    disk cache. Light colors are not part of the cache key: use a different ``cache`` name per rig.
    """
    width, height = int(size[0]), int(size[1])
    path = None
    if cache:
        path = Path(root or cache_root()) / cache / f"{_key(meshes, cam, (width, height))}.png"
        if path.exists():
            from PIL import Image

            return np.asarray(Image.open(path).convert("RGBA"))
    p = _plotter(width, height)
    p.clear_actors()
    for mesh, style in meshes:
        mirrored = mesh.copy()
        mirrored.points = np.asarray(mesh.points) * MIRROR
        # The mirror reverses face winding: reverse it back, so any normals VTK derives (smooth_shading
        # recomputes them) point outward again. Works for open surfaces too.
        mirrored.point_data.pop("Normals", None)
        mirrored = mirrored.extract_surface(algorithm="dataset_surface")
        mirrored.flip_faces(inplace=True)
        p.add_mesh(mirrored, **style)
    _lights(p, cam, palette or default_palette(), key_light, rim_light)
    match_camera(p, cam, design)
    p.render()  # without this the screenshot returns the previous frame's pixels
    rgba = np.asarray(p.screenshot(transparent_background=True, return_img=True), np.uint8)
    if rgba.shape[2] == 3:
        rgba = np.dstack([rgba, np.full(rgba.shape[:2], 255, np.uint8)])
    if path is not None:
        from PIL import Image

        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba, "RGBA").save(path, compress_level=1)
    return rgba


def composite(fr, rgba: np.ndarray, alpha: float = 1.0):
    """Draw a full-frame render into a Frame (any output size; it is stretched to the frame)."""
    if alpha <= 0.003:
        return
    img = skia.Image.fromarray(
        np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
    )
    fr.c.drawImageRect(img, skia.Rect.MakeWH(fr.dw, fr.dh), LINEAR, skia.Paint(AntiAlias=True, Alphaf=alpha))


def frame_size(fr) -> tuple[int, int]:
    """Render at the output resolution of the frame being drawn."""
    return fr.w, fr.h
