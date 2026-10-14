"""Renderer-owned offscreen VTK sessions; source geometry is never mutated."""

import numpy as np
from PIL import Image

from .camera import part_matrix
from .model import ArchDataError, pyvista


class ArchSession:
    def __init__(self, clip, factor=1):
        self.clip, self.factor = clip, factor
        self.plotter = None
        self.actors, self.meshes, self.contours = {}, {}, {}
        self.field_meshes = {}
        self._last_sections = {}
        try:
            pv = pyvista()
            theme = pv.themes.Theme()
            theme.multi_samples = 0
            self.plotter = pv.Plotter(
                off_screen=True,
                theme=theme,
                window_size=(max(1, round(clip.width * factor)), max(1, round(clip.height * factor))),
            )
            self.plotter.disable_anti_aliasing()
            self.plotter.render_window.SetMultiSamples(0)
            self.plotter.enable_depth_peeling()
            for part in clip.parts:
                style = part.style or clip.style
                mesh = part.mesh.dataset
                if style.concept == "topology":
                    mesh = mesh.extract_surface(algorithm="dataset_surface").triangulate()
                elif style.concept == "voxel":
                    estimate = np.prod(
                        np.maximum(
                            1, np.ceil((np.array(mesh.bounds)[1::2] - np.array(mesh.bounds)[::2]) / style.voxel_spacing)
                        )
                    )
                    if estimate > 2_000_000:
                        raise ArchDataError("voxel_spacing", "voxel budget exceeded; increase spacing")
                    mesh = mesh.voxelize(spacing=style.voxel_spacing)
                self.meshes[part.id] = mesh
                surface_style = (
                    "points"
                    if style.concept == "points"
                    else "wireframe"
                    if style.concept in {"wireframe", "blueprint"}
                    else "surface"
                )
                options = {
                    "color": style.edge_color if style.concept == "blueprint" else style.color,
                    "style": surface_style,
                    "opacity": style.opacity,
                    "line_width": style.line_width * factor,
                    "point_size": style.point_size * factor,
                    "show_edges": style.concept in {"topology", "voxel", "isometric"},
                    "edge_color": style.edge_color,
                    "smooth_shading": style.smooth_shading and surface_style == "surface",
                    "lighting": style.concept not in {"wireframe", "blueprint", "points"},
                    "show_scalar_bar": False,
                }
                if style.scalars:
                    options.update(
                        scalars=style.scalars, cmap=style.cmap, clim=style.clim, preference=style.association
                    )
                self.actors[part.id] = [self.plotter.add_mesh(mesh, **options)]
                if style.vectors:
                    field = mesh.cell_data_to_point_data() if style.association == "cell" else mesh
                    if style.field_mode == "glyphs":
                        # Deterministic bounded sampling avoids millions of glyphs.
                        ids = np.linspace(0, field.n_points - 1, min(256, field.n_points), dtype=int)
                        seeds = field.extract_points(ids, include_cells=False)
                        vectors = seeds.glyph(orient=style.vectors, scale=style.vectors, factor=0.15)
                    else:
                        vectors = field.streamlines(vectors=style.vectors, n_points=30, max_steps=500)
                    if vectors.n_points:
                        self.field_meshes[part.id] = vectors
                        self.actors[part.id].append(
                            self.plotter.add_mesh(vectors, color=style.edge_color, show_scalar_bar=False)
                        )
                self.contours[part.id] = self.plotter.add_mesh(pv.Line(), color=style.edge_color, line_width=2 * factor)
                self.contours[part.id].visibility = False
        except ArchDataError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise ArchDataError("render", f"Cannot initialize offscreen PyVista/VTK: {exc}") from exc

    def frame(self, age):
        try:
            return self._frame(age)
        except ArchDataError:
            raise
        except (RuntimeError, ValueError, TypeError, OSError) as exc:
            raise ArchDataError("render", f"Offscreen rendering failed: {exc}") from exc

    def _frame(self, age):
        clip = self.clip
        time = min(clip.duration, clip.source_start + max(0, age))
        state = clip.state_at(time)
        for part in clip.parts:
            s, style = state["parts"][part.id], part.style or clip.style
            matrix = part_matrix(s)
            for index, actor in enumerate(self.actors[part.id]):
                actor.user_matrix = matrix
                actor.visibility = s["visible"]
                actor.prop.opacity = s["opacity"] * (0.24 if style.concept in {"transparent", "xray"} else 1)
                if index:
                    actor.prop.color = s["color"] if s["highlighted"] else style.edge_color
                elif not style.scalars:
                    actor.prop.color = (
                        style.edge_color if style.concept == "blueprint" and not s["highlighted"] else s["color"]
                    )
                else:
                    actor.prop.show_edges = s["highlighted"] or style.concept in {"topology", "isometric"}
                    actor.prop.edge_color = s["color"] if s["highlighted"] else style.edge_color
                    actor.prop.point_size = style.point_size * self.factor * (1.5 if s["highlighted"] else 1)
            section = s["section"]
            section_key = (repr(section), matrix.tobytes()) if section else None
            if section_key != self._last_sections.get(part.id):
                mesh = self.meshes[part.id]
                if section:
                    inv = np.linalg.inv(matrix)
                    origin = (inv @ np.array([*section["origin"], 1]))[:3]
                    normal = matrix[:3, :3].T @ np.asarray(section["normal"])
                    if section["cap"]:
                        clipped = (
                            mesh.extract_surface(algorithm="dataset_surface")
                            .triangulate()
                            # Closed-surface clipping keeps the positive half-space.
                            .clip_closed_surface(normal=-normal, origin=origin)
                        )
                    else:
                        clipped = mesh.clip(normal=normal, origin=origin, invert=True)
                    self.actors[part.id][0].mapper.dataset = clipped
                    if part.id in self.field_meshes:
                        self.actors[part.id][1].mapper.dataset = self.field_meshes[part.id].clip(
                            normal=normal, origin=origin, invert=True
                        )
                    line = mesh.slice(normal=normal, origin=origin)
                    self.contours[part.id].mapper.dataset = line
                    self.contours[part.id].visibility = section["contour"] and s["visible"] and bool(line.n_points)
                else:
                    self.actors[part.id][0].mapper.dataset = mesh
                    if part.id in self.field_meshes:
                        self.actors[part.id][1].mapper.dataset = self.field_meshes[part.id]
                    self.contours[part.id].visibility = False
                self._last_sections[part.id] = section_key
            self.contours[part.id].user_matrix = matrix
            if section:
                self.contours[part.id].visibility = (
                    s["visible"] and section["contour"] and bool(self.contours[part.id].mapper.dataset.n_points)
                )
        camera = state["camera"]
        c = self.plotter.camera
        c.position, c.focal_point, c.up = camera.position, camera.focal_point, camera.up
        c.parallel_projection = camera.projection == "orthographic"
        c.parallel_scale = clip.parallel_scale / camera.zoom
        import math

        c.view_angle = math.degrees(2 * math.atan(math.tan(math.radians(camera.view_angle / 2)) / camera.zoom))
        self.plotter.reset_camera_clipping_range()
        # Screenshot reads the framebuffer; subsequent state changes need a render.
        self.plotter.render()
        pixels = self.plotter.screenshot(transparent_background=True, return_img=True)
        image = Image.fromarray(np.array(pixels, copy=True), "RGBA")
        image.alpha_composite(clip.annotation_overlay(time, self.factor))
        return image

    def close(self):
        if self.plotter is not None:
            self.plotter.close()
            self.plotter = None
        self.actors.clear()
        self.meshes.clear()
        self.field_meshes.clear()
        self.contours.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
