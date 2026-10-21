"""Deterministic layouts and shared paths for strokes, ports and motion."""

import math
from itertools import pairwise

from facelesschamp_kit.diagrams.model import FlowDataError


def layers(graph):
    """Tarjan SCC condensation followed by stable longest-path ranks."""
    adjacency = {n.id: [] for n in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source].append(edge.target)
    indices, low, stack, active, groups = {}, {}, [], set(), []

    def visit(node):
        indices[node] = low[node] = len(indices)
        stack.append(node)
        active.add(node)
        for other in adjacency[node]:
            if other not in indices:
                visit(other)
                low[node] = min(low[node], low[other])
            elif other in active:
                low[node] = min(low[node], indices[other])
        if low[node] == indices[node]:
            group = []
            while True:
                other = stack.pop()
                active.remove(other)
                group.append(other)
                if other == node:
                    break
            groups.append(group)

    for node in adjacency:
        if node not in indices:
            visit(node)
    membership = {node: i for i, group in enumerate(groups) for node in group}
    parents = {i: set() for i in range(len(groups))}
    for edge in graph.edges:
        a, b = membership[edge.source], membership[edge.target]
        if a != b:
            parents[b].add(a)
    ranks = {}

    def rank(i):
        if i not in ranks:
            ranks[i] = max((rank(p) + 1 for p in parents[i]), default=0)
        return ranks[i]

    result = {}
    for node in graph.nodes:
        result.setdefault(rank(membership[node.id]), []).append(node.id)
    return [result[r] for r in sorted(result)]


def layout_graph(graph, width, height):
    positions = {}
    count = len(graph.nodes)
    if graph.layout == "manual":
        if any(n.position is None for n in graph.nodes):
            raise FlowDataError("layout", "manual layout requires every node position")
    elif graph.layout == "grid":
        cols = max(1, math.ceil(math.sqrt(count * width / height)))
        rows = math.ceil(count / cols)
        for i, node in enumerate(graph.nodes):
            positions[node.id] = ((i % cols + 0.5) * width / cols, (i // cols + 0.5) * height / rows)
    elif graph.layout == "radial":
        for i, node in enumerate(graph.nodes):
            angle = -math.pi / 2 + 2 * math.pi * i / count
            positions[node.id] = (
                (width / 2 + width * 0.32 * math.cos(angle), height / 2 + height * 0.32 * math.sin(angle))
                if count > 1
                else (width / 2, height / 2)
            )
    else:
        groups = layers(graph)
        horizontal = graph.direction == "horizontal"
        for i, group in enumerate(groups):
            for j, id in enumerate(group):
                u, v = (i + 0.5) / len(groups), (j + 0.5) / len(group)
                positions[id] = (u * width, v * height) if horizontal else (v * width, u * height)
    positions.update({n.id: n.position for n in graph.nodes if n.position is not None})
    return positions


def transform(p, state):
    angle = math.radians(state["rotation"])
    x, y = (v * state["scale"] for v in p)
    cx, cy = state["position"]
    return (cx + x * math.cos(angle) - y * math.sin(angle), cy + x * math.sin(angle) + y * math.cos(angle))


def port(node, state, id, destination):
    w, h = node.size
    if id is not None:
        p = next(p for p in node.ports if p.id == id)
        x, y = {
            "left": (-w / 2, (p.offset - 0.5) * h),
            "right": (w / 2, (p.offset - 0.5) * h),
            "top": ((p.offset - 0.5) * w, -h / 2),
            "bottom": ((p.offset - 0.5) * w, h / 2),
            "center": (0, 0),
        }[p.side]
    else:
        cx, cy = state["position"]
        angle = -math.radians(state["rotation"])
        dx, dy = destination[0] - cx, destination[1] - cy
        dx, dy = dx * math.cos(angle) - dy * math.sin(angle), dx * math.sin(angle) + dy * math.cos(angle)
        if abs(dx) + abs(dy) < 1e-9:
            dx = 1
        if node.symbol == "circle":
            ratio = 1 / math.sqrt((dx / (w / 2)) ** 2 + (dy / (h / 2)) ** 2)
        elif node.symbol == "diamond":
            ratio = 1 / (abs(dx) / (w / 2) + abs(dy) / (h / 2))
        else:
            ratio = 1 / max(abs(dx) / (w / 2), abs(dy) / (h / 2))
        x, y = dx * ratio, dy * ratio
    if id is not None and (x or y) and node.symbol in {"circle", "diamond"}:
        divisor = (
            math.sqrt((x / (w / 2)) ** 2 + (y / (h / 2)) ** 2)
            if node.symbol == "circle"
            else abs(x) / (w / 2) + abs(y) / (h / 2)
        )
        x, y = x / divisor, y / divisor
    return transform((x, y), state)


def port_lead(node, state, id, endpoint):
    if id is None:
        return endpoint
    side = next(p.side for p in node.ports if p.id == id)
    dx, dy = {"left": (-20, 0), "right": (20, 0), "top": (0, -20), "bottom": (0, 20), "center": (0, 0)}[side]
    angle = math.radians(state["rotation"])
    return (
        endpoint[0] + dx * math.cos(angle) - dy * math.sin(angle),
        endpoint[1] + dx * math.sin(angle) + dy * math.cos(angle),
    )


def edge_path(edge, nodes, states):
    a, b = states[edge.source], states[edge.target]
    start = port(nodes[edge.source], a, edge.source_port, b["position"])
    end = port(nodes[edge.target], b, edge.target_port, a["position"])
    if edge.source == edge.target and not edge.waypoints:
        n = nodes[edge.source]
        if edge.source_port is None:
            start = transform((n.size[0] / 2, 0), a)
        if edge.target_port is None:
            end = transform((0, -n.size[1] / 2), a)
        return [start, (start[0] + 45, start[1]), (start[0] + 45, end[1] - 45), (end[0], end[1] - 45), end]
    if edge.route == "bezier":
        controls = edge.waypoints or (
            (start[0] + (end[0] - start[0]) * 0.5, start[1]),
            (end[0] - (end[0] - start[0]) * 0.5, end[1]),
        )
        a, b, c, d = start, *controls, end
        # Fixed subdivision keeps random access and length sampling deterministic.
        return [
            tuple(
                (1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * b[k] + 3 * (1 - t) * t * t * c[k] + t**3 * d[k]
                for k in (0, 1)
            )
            for t in (i / 96 for i in range(97))
        ]
    if edge.route == "straight":
        return [start, *edge.waypoints, end]
    first = port_lead(nodes[edge.source], a, edge.source_port, start)
    last = port_lead(nodes[edge.target], b, edge.target_port, end)
    anchors = [first, *edge.waypoints, last]
    result = [start, first]
    for a, b in pairwise(anchors):
        if abs(b[0] - a[0]) >= abs(b[1] - a[1]):
            middle = (a[0] + b[0]) / 2
            result.extend(((middle, a[1]), (middle, b[1]), b))
        else:
            middle = (a[1] + b[1]) / 2
            result.extend(((a[0], middle), (b[0], middle), b))
    result.append(end)
    return result


def length(points):
    return sum(math.dist(a, b) for a, b in pairwise(points))


def sample(points, progress):
    distance = length(points) * max(0, min(1, progress))
    for a, b in pairwise(points):
        span = math.dist(a, b)
        if span > 0 and distance <= span:
            t = distance / span
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        distance -= span
    return points[-1]


def prefix(points, progress):
    distance = length(points) * max(0, min(1, progress))
    result = [points[0]]
    for a, b in pairwise(points):
        span = math.dist(a, b)
        if span and distance < span:
            result.append((a[0] + (b[0] - a[0]) * distance / span, a[1] + (b[1] - a[1]) * distance / span))
            break
        result.append(b)
        distance -= span
    return result
