"""Twenty-second, graphics-only toroidal fusion plasma; native PyVista + Faceless Champ."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/faceless-fusion-matplotlib")

import numpy as np
import pyvista as pv
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageEnhance

from faceless_champ import Canvas, ExportProgress, ExportSettings, Scene, render

ROOT = Path(__file__).resolve().parent
DURATION = 20.0
MAJOR_RADIUS = 3.0


def smooth(value):
    x = np.clip(value, 0, 1)
    return x * x * (3 - 2 * x)


def torus_points(u, v, radius):
    """Toroidal coordinates, with a slightly elongated poloidal section."""
    return np.column_stack(
        (
            (MAJOR_RADIUS + radius * np.cos(v)) * np.cos(u),
            (MAJOR_RADIUS + radius * np.cos(v)) * np.sin(u),
            1.12 * radius * np.sin(v),
        )
    )


def make_grid():
    grid = pv.ImageData(dimensions=(112, 112, 44), spacing=(0.08, 0.08, 0.065), origin=(-4.44, -4.44, -1.3975))
    x, y, z = grid.points.T
    radial = np.hypot(x, y)
    return grid, (radial - MAJOR_RADIUS, np.arctan2(y, x), z / 1.12)


def energy_density(coords, t):
    """Analytic, source-time scalar animation; an illustrative field, not an MHD solve."""
    radial, phi, z = coords
    ignition = 0.16 + 0.84 * smooth((t - 1.5) / 4)
    activity = smooth((t - 5) / 4)
    pulse = np.exp(-(((t - 15.5) / 1.7) ** 2))
    displacement = 0.055 * activity
    dr = radial - displacement * np.cos(3 * phi - 1.35 * t)
    dz = z - displacement * np.sin(3 * phi - 1.35 * t)
    rho = np.hypot(dr, dz)
    theta = np.arctan2(dz, dr)
    width = 0.35 + 0.035 * np.sin(0.75 * t) + 0.075 * pulse
    core = np.exp(-((rho / width) ** 2))
    wave = 0.76 + 0.15 * np.cos(3 * phi - 1.6 * t + 2 * theta)
    wave += 0.09 * np.sin(7 * phi + 3 * theta + 2.1 * t)
    # A broad traveling hot region and fine braided structure remain inside the torus.
    hotspot = np.exp(4 * (np.cos(phi - 0.82 * t) - 1)) * np.exp(-((rho / 0.55) ** 2))
    density = ignition * (core * wave + 0.23 * activity * hotspot + 0.18 * pulse * core)
    density *= 1 - smooth((rho - 0.66) / 0.14)
    return np.clip(density, 0, 1.2).astype(np.float32)


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    scene.wait_until(DURATION)
    return scene


class FusionRenderer:
    """Faceless Champ Renderer protocol; owns all native VTK resources locally.

    Persistent volume/scalar buffers are updated in place. No per-frame plotters,
    meshes in timeline snapshots, temporary image sequences, or external assets.
    """

    def __init__(self):
        self.plotter = None
        self.grid, self.coords = make_grid()
        self.grid["energy"] = energy_density(self.coords, 0)
        self.contour_mesh = pv.PolyData()
        self.fields = []
        self.chamber = []
        self.identity = {"backend": "pyvista", "pyvista": pv.__version__, "vtk": pv.vtk_version_info}

    def validate(self, scene):
        if scene.duration != DURATION or scene.canvas.bg != "#000000":
            raise ValueError("Expected the 20-second black fusion timeline")

    def _initialize(self, size):
        theme = pv.themes.Theme()
        theme.multi_samples = 0
        self.plotter = p = pv.Plotter(off_screen=True, window_size=size, theme=theme)
        p.set_background("#000000")
        p.render_window.SetMultiSamples(0)
        # Standard alpha composition preserves GPU volume color on native EGL.
        p.disable_depth_peeling()

        u, v = np.meshgrid(np.linspace(0, math.tau, 181), np.linspace(0, math.tau, 49), indexing="ij")
        xyz = torus_points(u.ravel(), v.ravel(), 0.94)
        shell = pv.StructuredGrid(*(xyz[:, i].reshape(u.shape) for i in range(3))).extract_surface(
            algorithm="dataset_surface"
        )
        self.chamber.append(
            (p.add_mesh(shell, color="#258EAD", opacity=0.045, smooth_shading=True, show_scalar_bar=False), 0.045)
        )
        for phi in np.linspace(0, math.tau, 18, endpoint=False):
            theta = np.linspace(0, math.tau, 129)
            rib = pv.lines_from_points(torus_points(np.full_like(theta, phi), theta, 0.96))
            self.chamber.append((p.add_mesh(rib, color="#5591A8", line_width=1.5, opacity=0.35, lighting=False), 0.35))
        # Chamber equatorial rails define the toroidal enclosure without occluding plasma.
        for radius in (MAJOR_RADIUS - 0.96, MAJOR_RADIUS + 0.96):
            phi = np.linspace(0, math.tau, 361)
            rail = pv.lines_from_points(np.column_stack((radius * np.cos(phi), radius * np.sin(phi), 0 * phi)))
            self.chamber.append((p.add_mesh(rail, color="#6BBDD0", opacity=0.55, line_width=2, lighting=False), 0.55))

        # Nested magnetic flux surfaces: closed helical field lines on three radii.
        for layer, radius in enumerate((0.76, 1.04, 1.22)):
            for phase in np.linspace(0, math.tau, 3, endpoint=False):
                phi = np.linspace(0, 2 * math.tau, 721)
                theta = 1.5 * phi + phase
                line = pv.lines_from_points(torus_points(phi, theta, radius))
                actor = p.add_mesh(
                    line, color=("#50D6EA", "#329EC7", "#246383")[layer], line_width=1.2, opacity=0.5, lighting=False
                )
                self.fields.append((actor, 0.6 - layer * 0.14))

        cmap = LinearSegmentedColormap.from_list(
            "fusion", ["#16062C", "#60148A", "#D029B9", "#FF6248", "#FFB545", "#FFF2BC", "#FFFFFF"]
        )
        opacity = np.interp(np.linspace(0, 1.2, 256), [0, 0.04, 0.16, 0.4, 0.8, 1.2], [0, 0, 0.018, 0.1, 0.3, 0.55])
        # A full 256-entry PyVista LUT uses byte alpha, unlike shorter opacity lists.
        opacity = np.round(opacity * 255).astype(np.uint8)
        self.volume = p.add_volume(
            self.grid,
            scalars="energy",
            cmap=cmap,
            clim=(0, 1.2),
            opacity=opacity,
            blending="composite",
            mapper="gpu",
            shade=False,
            show_scalar_bar=False,
            opacity_unit_distance=0.2,
        )
        self.volume.mapper.dataset = self.grid
        self.volume.prop.interpolation_type = "linear"
        # Seed a nonempty mesh before the first (potentially unignited) frame.
        seed = self.grid.copy()
        seed["energy"] = energy_density(self.coords, 10)
        self.contour_mesh.copy_from(seed.contour([0.45, 0.8], scalars="energy"))
        self.contour_actor = p.add_mesh(
            self.contour_mesh,
            color="#FF8C80",
            opacity=0.035,
            smooth_shading=True,
            show_scalar_bar=False,
            lighting=False,
        )
        self.front = pv.PolyData(np.zeros((100, 3)))
        self.front_actor = p.add_mesh(
            self.front, color="#D1FAFF", point_size=3, render_points_as_spheres=True, lighting=False
        )
        p.camera.parallel_projection = True
        p.camera.parallel_scale = 4.45
        p.camera.up = (0, 0, 1)
        self.identity["render_window"] = p.render_window.GetClassName()

    def frame(self, scene, time, size):
        if not math.isfinite(time) or not 0 <= time <= DURATION:
            raise ValueError("Source time must be in [0, 20]")
        if self.plotter is None:
            self._initialize(size)
        p = self.plotter
        p.window_size = size
        self.grid["energy"][:] = energy_density(self.coords, time)
        self.grid.GetPointData().GetScalars().Modified()
        self.grid.Modified()
        level = 0.01 + 0.025 * smooth((time - 5) / 4)
        contours = self.grid.contour([0.45, 0.8], scalars="energy")
        self.contour_actor.visibility = bool(contours.n_points)
        if contours.n_points:
            self.contour_mesh.copy_from(contours)
        self.contour_actor.prop.opacity = level
        field_reveal = float(smooth(time / 2))
        for actor, opacity in self.fields:
            actor.prop.opacity = opacity * field_reveal * (0.87 + 0.13 * math.sin(time * 0.9))
        for actor, opacity in self.chamber:
            actor.prop.opacity = opacity * (1 - 0.4 * float(smooth((time - 4) / 4)))
        # Small moving packets make the direction of the confinement field visible.
        ids = np.arange(100)
        phi = ids * (math.tau / 25) + 0.62 * time
        theta = 1.5 * phi + (ids // 25) * math.tau / 4
        self.front.points = torus_points(phi, theta, 1.045)
        self.front_actor.prop.opacity = 0.75 * field_reveal
        azimuth = math.radians(-58 + time * 1.8)
        p.camera.position = (11 * math.cos(azimuth), 11 * math.sin(azimuth), 7 + 0.6 * math.sin(time * 0.14))
        p.camera.focal_point = (0, 0, 0)
        p.reset_camera_clipping_range()
        p.render()
        pixels = p.screenshot(return_img=True, transparent_background=False)
        image = Image.fromarray(np.array(pixels, copy=True)).convert("RGB")
        envelope = float(smooth(time / 0.8) * smooth((DURATION - time) / 1.0))
        return ImageEnhance.Brightness(image).enhance(envelope)

    def close(self):
        if self.plotter is not None:
            self.plotter.close()
            self.plotter = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="One-second sample at source time 10–11")
    mode.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error("frame must be in [0, 20]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 20")
    if args.fps < 1:
        parser.error("fps must be positive")
    filename = (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else ("preview.mp4" if args.preview else "pyvista-fusion.mp4")
    )
    output = args.output or ROOT / "output" / filename
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite")
    if output.suffix.lower() != (".png" if args.frame is not None else ".mp4"):
        parser.error("use .png for frames and .mp4 for movies")
    output.parent.mkdir(parents=True, exist_ok=True)
    settings = ExportSettings(quality=args.quality, fps=args.fps, antialias=1)
    source_range = args.range or ([10, 11] if args.preview else [0, DURATION])
    scene = build_scene()
    with FusionRenderer() as renderer:
        renderer.validate(scene)
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            renderer.frame(scene, args.frame, settings.dimensions(scene.canvas)).save(output)
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    renderer=renderer,
                    overwrite=args.overwrite,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    progress=progress,
                )
        evidence = {
            "scene_duration": scene.duration,
            "source_range": source_range,
            "rendering": renderer.identity,
            "full_export_verified": False,
            "illustrative_field": True,
            "audio": False,
        }
    output.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
