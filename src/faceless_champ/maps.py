"""Offline geographic components. Install ``faceless-champ[maps]`` to render them."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from .animation import AnimationBuilder
from .components import Component, finite

ASSETS = Path(__file__).parent / "assets" / "maps"
OCEANS = {
    "pacific ocean": (-160, 0, 140, 120),
    "atlantic ocean": (-30, 0, 80, 140),
    "indian ocean": (80, -25, 90, 90),
    "arctic ocean": (0, 90, 360, 35),
    "southern ocean": (0, -75, 360, 30),
}


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError('Map rendering requires: pip install "faceless-champ[maps]"') from exc
    return np


@lru_cache(maxsize=1)
def _countries():
    return json.loads((ASSETS / "countries.json").read_text())


def supported_countries():
    """Return bundled country names, sorted alphabetically."""
    return tuple(sorted(c["name"] for c in _countries()))


def _country(name):
    if not isinstance(name, str):
        raise TypeError("Country must be a name or ISO code")
    key = name.strip().casefold()
    for country in _countries():
        if key in (alias.casefold() for alias in country["aliases"]):
            return country
    raise ValueError(f"Unknown country {name!r}; use supported_countries() for available names")


def _bounds(country):
    points = [p for poly in country["polygons"] for ring in poly for p in ring]
    xs = sorted({p[0] % 360 for p in points})
    gaps = [(xs[(i + 1) % len(xs)] + (360 if i == len(xs) - 1 else 0) - x, i) for i, x in enumerate(xs)]
    gap, i = max(gaps)
    start = xs[(i + 1) % len(xs)]
    span = 360 - gap
    ys = [p[1] for p in points]
    return (
        (start + span / 2 + 180) % 360 - 180,
        (min(ys) + max(ys)) / 2,
        max(span, 0.01),
        max(max(ys) - min(ys), 0.01),
    )


def _latitude(value):
    value = finite(value, "latitude")
    if not -90 <= value <= 90:
        raise ValueError("latitude must be between -90 and 90")
    return value


class MapAnimationBuilder(AnimationBuilder):
    def __init__(self, component):
        super().__init__(component)
        self.map_shortest = False

    def zoom_to(self, target, *, zoom=None):
        if any(k in self.targets for k in ("longitude", "latitude")):
            raise ValueError("Use separate play calls for geographic rotation and zoom_to")
        self.targets.update(self.component._target(target, zoom))
        self.map_shortest = True
        return self

    def rotate(self, degrees=None, *, longitude=None, latitude=None):
        values = self.component._rotation(degrees, longitude, latitude)
        if set(values) & self.targets.keys():
            raise ValueError("Map rotation properties already set in this animation")
        self.targets.update(values)
        self.relative += tuple(values)
        return self


class Map(Component):
    """Shared fixed-viewport map behavior; use one of the three concrete classes."""

    def __init__(self, *, width=800, height=400, longitude=0, latitude=0, zoom=1, **kwargs):
        super().__init__(**kwargs)
        self.width = finite(width, "width", 1)
        self.height = finite(height, "height", 1)
        self.longitude = finite(longitude, "longitude")
        self.latitude = _latitude(latitude)
        self.zoom = finite(zoom, "zoom", 0.001)
        self.map_rotation = 0.0

    @property
    def animate(self):
        return MapAnimationBuilder(self)

    def state(self):
        return dict(
            super().state(),
            longitude=self.longitude,
            latitude=self.latitude,
            zoom=self.zoom,
            map_rotation=self.map_rotation,
        )

    def _target(self, target, zoom):
        if not isinstance(target, str):
            raise TypeError("Target must be a country name, ISO code, or ocean name")
        region = OCEANS.get(target.strip().casefold())
        lon, lat, dx, dy = region if region else _bounds(_country(target))
        if zoom is None:
            if isinstance(self, EarthMap):
                # Frame angular extent, conservatively including distant islands.
                extent = max(dx * math.cos(math.radians(lat)), dy)
                zoom = 0.85 / math.sin(math.radians(min(180, max(0.01, extent)) / 2))
            else:
                unit = min(self.width / 360, self.height / 180)
                zoom = 0.85 * min(self.width / (unit * dx), self.height / (unit * dy))
        return {"longitude": lon, "latitude": lat, "zoom": finite(zoom, "zoom", 0.001)}

    def zoom_to(self, target, *, zoom=None):
        for key, value in self._target(target, zoom).items():
            setattr(self, key, value)
        return self

    def _rotation(self, degrees, longitude, latitude):
        if isinstance(self, EarthMap):
            if degrees is not None or (longitude is None and latitude is None):
                raise TypeError("EarthMap.rotate requires longitude= and/or latitude= degree offsets")
            return {k: finite(v, k) for k, v in [("longitude", longitude), ("latitude", latitude)] if v is not None}
        if degrees is None or longitude is not None or latitude is not None:
            raise TypeError("Flat map rotate requires a degree offset")
        return {"map_rotation": finite(degrees, "degrees")}

    def rotate(self, degrees=None, *, longitude=None, latitude=None):
        values = self._rotation(degrees, longitude, latitude)
        if "latitude" in values:
            _latitude(self.latitude + values["latitude"])
        for key, value in values.items():
            setattr(self, key, getattr(self, key) + value)
        return self


class OutlineMap(Map):
    def __init__(self, country=None, *, fill=None, border_color="white", border_width=1, **kwargs):
        super().__init__(**kwargs)
        self.country = None if country is None else _country(country)["name"]
        self.fill = fill
        self.border_color = border_color
        self.border_width = finite(border_width, "border_width", 0)
        for color in (fill, border_color):
            if color is not None:
                ImageColor.getcolor(color, "RGBA")
        if country is not None:
            self.zoom_to(country)


class SatelliteMap(Map):
    pass


class EarthMap(Map):
    def __init__(self, *, width=600, height=600, **kwargs):
        super().__init__(width=width, height=height, **kwargs)


@lru_cache(maxsize=1)
def _texture():
    np = _numpy()
    with Image.open(ASSETS / "earth.jpg") as source:
        return np.asarray(source.convert("RGB"))


def _outline(c, state, size, factor):
    result = Image.new("RGBA", size)
    unit = min(size[0] / 360, size[1] / 180) * state["zoom"]
    theta = math.radians(state["map_rotation"] % 360)
    co, si = math.cos(theta), math.sin(theta)
    countries = [_country(c.country)] if c.country else _countries()
    center = (state["longitude"] + 180) % 360 - 180
    for country in countries:
        for polygon in country["polygons"]:
            # Unwrap each ring before projecting so date-line islands stay intact.
            rings = []
            for ring in polygon:
                unwrapped = [ring[0]]
                for x, y in ring[1:]:
                    previous = unwrapped[-1][0]
                    unwrapped.append((previous + (x - previous + 180) % 360 - 180, y))
                rings.append(unwrapped)
            middle = sum(p[0] for p in rings[0]) / len(rings[0])
            base = round((center - middle) / 360)
            # Only copies intersecting the viewport can contribute, even when zoomed out.
            radius = math.hypot(*size) / (2 * unit)
            copies = math.ceil(radius / 360) + 1
            for offset in range(base - copies, base + copies + 1):
                projected = []
                for ring in rings:
                    pts = []
                    for x, y in ring:
                        x, y = (x + offset * 360 - center) * unit, (state["latitude"] - y) * unit
                        pts.append((size[0] / 2 + co * x - si * y, size[1] / 2 + si * x + co * y))
                    projected.append(pts)
                xs, ys = zip(*projected[0])
                if max(xs) < 0 or min(xs) > size[0] or max(ys) < 0 or min(ys) > size[1]:
                    continue
                if c.fill is not None:
                    mask = Image.new("L", size)
                    draw = ImageDraw.Draw(mask)
                    for i, ring in enumerate(projected):
                        draw.polygon(ring, fill=255 if i == 0 else 0)
                    layer = Image.new("RGBA", size, c.fill)
                    if layer.getpixel((0, 0))[3] != 255:
                        alpha = layer.getpixel((0, 0))[3]
                        mask = mask.point(lambda v, alpha=alpha: round(v * alpha / 255))
                    layer.putalpha(mask)
                    result.alpha_composite(layer)
                if c.border_color is not None and c.border_width:
                    draw = ImageDraw.Draw(result)
                    for ring in projected:
                        draw.line(
                            ring, fill=c.border_color, width=max(1, round(c.border_width * factor)), joint="curve"
                        )
    return result


def draw_map(c, state, factor):
    np = _numpy()
    size = (max(1, round(c.width * factor)), max(1, round(c.height * factor)))
    if isinstance(c, OutlineMap):
        return _outline(c, state, size, factor)
    texture = _texture()
    th, tw = texture.shape[:2]
    result = Image.new("RGBA", size)
    # Row strips cap temporary projection arrays independently of output height.
    for top in range(0, size[1], 64):
        yy, xx = np.mgrid[top : min(top + 64, size[1]), : size[0]].astype(np.float64)
        xx += 0.5 - size[0] / 2
        yy = size[1] / 2 - yy - 0.5
        lon0, lat0 = np.radians([state["longitude"] % 360, state["latitude"]])
        if isinstance(c, EarthMap):
            radius = min(size) * 0.48 * state["zoom"]
            x, y = xx / radius, yy / radius
            rr = x * x + y * y
            valid = rr <= 1
            z = np.sqrt(np.maximum(0, 1 - rr))
            lat = np.arcsin(np.clip(y * np.cos(lat0) + z * np.sin(lat0), -1, 1))
            lon = lon0 + np.arctan2(x, z * np.cos(lat0) - y * np.sin(lat0))
            light = 0.35 + 0.65 * np.clip(-0.3 * x + 0.4 * y + 0.8660254 * z, 0, 1)
        else:
            unit = min(size[0] / 360, size[1] / 180) * state["zoom"]
            angle = math.radians(state["map_rotation"] % 360)
            lon = lon0 + np.radians((xx * math.cos(angle) - yy * math.sin(angle)) / unit)
            lat = lat0 + np.radians((xx * math.sin(angle) + yy * math.cos(angle)) / unit)
            valid = np.abs(lat) <= np.pi / 2
            light = 1
        u = ((lon / (2 * np.pi) + 0.5) * tw - 0.5) % tw
        v = np.clip((0.5 - lat / np.pi) * th - 0.5, 0, th - 1)
        x0, y0 = np.floor(u).astype(int) % tw, np.floor(v).astype(int)
        x1, y1 = (x0 + 1) % tw, np.minimum(y0 + 1, th - 1)
        fx, fy = (u - np.floor(u))[..., None], (v - y0)[..., None]
        rgb = (texture[y0, x0] * (1 - fx) + texture[y0, x1] * fx) * (1 - fy) + (
            texture[y1, x0] * (1 - fx) + texture[y1, x1] * fx
        ) * fy
        if isinstance(c, EarthMap):
            rgb *= light[..., None]
        rgba = np.empty((*valid.shape, 4), dtype=np.uint8)
        rgba[..., :3] = np.rint(np.clip(rgb, 0, 255)).astype(np.uint8)
        rgba[..., 3] = valid.astype(np.uint8) * 255
        result.paste(Image.fromarray(rgba), (0, top))
    return result
