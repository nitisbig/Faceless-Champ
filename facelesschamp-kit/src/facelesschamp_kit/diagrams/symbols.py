"""Built-in vector strokes in normalized node coordinates."""

import math


def arc(cx, cy, rx, ry, start=0, end=360, steps=48):
    return [
        (
            cx + rx * math.cos(math.radians(start + (end - start) * i / steps)),
            cy + ry * math.sin(math.radians(start + (end - start) * i / steps)),
        )
        for i in range(steps + 1)
    ]


def symbol_paths(symbol):
    rect = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5), (-0.5, -0.5)]
    if symbol in {"circle", "junction"}:
        return [arc(0, 0, 0.5, 0.5)]
    if symbol == "diamond":
        return [[(0, -0.5), (0.5, 0), (0, 0.5), (-0.5, 0), (0, -0.5)]]
    if symbol in {"rounded_rectangle", "service"}:
        return [
            arc(0.38, -0.32, 0.12, 0.18, 270, 360, 8)
            + arc(0.38, 0.32, 0.12, 0.18, 0, 90, 8)
            + arc(-0.38, 0.32, 0.12, 0.18, 90, 180, 8)
            + arc(-0.38, -0.32, 0.12, 0.18, 180, 270, 8)
            + [(0.38, -0.5)]
        ]
    if symbol == "document":
        return [
            [(-0.5, 0.35), (-0.5, -0.5), (0.5, -0.5), (0.5, 0.35)]
            + [(x / 40 - 0.5, 0.35 + 0.12 * math.sin(x / 40 * 2 * math.pi)) for x in range(40, -1, -1)]
        ]
    if symbol == "database":
        return [
            arc(0, -0.32, 0.5, 0.18),
            [(-0.5, -0.32), (-0.5, 0.32)],
            [(0.5, -0.32), (0.5, 0.32)],
            arc(0, 0.32, 0.5, 0.18, 0, 180),
        ]
    if symbol == "queue":
        return [rect, *[[(x, -0.5), (x, 0.5)] for x in (-0.25, 0, 0.25)]]
    if symbol == "server":
        return [
            rect,
            [(-0.5, -0.17), (0.5, -0.17)],
            [(-0.5, 0.17), (0.5, 0.17)],
            *[[(0.34, y), (0.4, y)] for y in (-0.33, 0, 0.33)],
        ]
    if symbol == "client":
        return [
            [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.22), (-0.5, 0.22), (-0.5, -0.5)],
            [(0, 0.22), (0, 0.5)],
            [(-0.25, 0.5), (0.25, 0.5)],
        ]
    if symbol == "router":
        return [
            rect,
            [(-0.3, 0), (0.3, 0)],
            [(0.17, -0.12), (0.3, 0), (0.17, 0.12)],
            [(-0.17, -0.12), (-0.3, 0), (-0.17, 0.12)],
        ]
    if symbol == "resistor":
        return [
            [
                (-0.5, 0),
                (-0.35, 0),
                (-0.28, -0.25),
                (-0.14, 0.25),
                (0, -0.25),
                (0.14, 0.25),
                (0.28, -0.25),
                (0.35, 0),
                (0.5, 0),
            ]
        ]
    if symbol in {"capacitor", "battery"}:
        return [
            [(-0.5, 0), (-0.09, 0)],
            [(0.09, 0), (0.5, 0)],
            [(-0.09, -0.4), (-0.09, 0.4)],
            [(0.09, -0.4 if symbol == "capacitor" else -0.22), (0.09, 0.4 if symbol == "capacitor" else 0.22)],
        ]
    if symbol == "ground":
        return [[(0, -0.5), (0, 0)], [(-0.4, 0), (0.4, 0)], [(-0.27, 0.2), (0.27, 0.2)], [(-0.12, 0.4), (0.12, 0.4)]]
    if symbol == "switch":
        return [[(-0.5, 0), (-0.25, 0), (0.25, -0.35)], [(0.25, 0), (0.5, 0)]]
    if symbol in {"diode", "led"}:
        paths = [
            [(-0.5, 0), (-0.2, 0)],
            [(-0.2, -0.3), (0.2, 0), (-0.2, 0.3), (-0.2, -0.3)],
            [(0.2, -0.3), (0.2, 0.3)],
            [(0.2, 0), (0.5, 0)],
        ]
        if symbol == "led":
            paths += [[(0.05, -0.32), (0.2, -0.5), (0.12, -0.48)], [(0.25, -0.22), (0.4, -0.4), (0.32, -0.38)]]
        return paths
    if symbol == "and":
        return [[(-0.5, -0.5), (0, -0.5)] + arc(0, 0, 0.5, 0.5, -90, 90) + [(-0.5, 0.5), (-0.5, -0.5)]]
    if symbol == "or":

        def quadratic(a, b, c):
            return [
                tuple((1 - t) ** 2 * a[k] + 2 * (1 - t) * t * b[k] + t * t * c[k] for k in (0, 1))
                for t in (i / 32 for i in range(33))
            ]

        return [
            quadratic((-0.5, -0.5), (0.2, -0.5), (0.5, 0))
            + quadratic((0.5, 0), (0.2, 0.5), (-0.5, 0.5))
            + quadratic((-0.5, 0.5), (-0.15, 0), (-0.5, -0.5))
        ]
    if symbol == "not":
        return [[(-0.5, -0.5), (0.3, 0), (-0.5, 0.5), (-0.5, -0.5)], arc(0.4, 0, 0.1, 0.12)]
    return [rect]
