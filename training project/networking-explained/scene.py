"""Networking Explained: approved FlowDesign, authored topology and story timing."""

from __future__ import annotations

from dataclasses import replace

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowBackdrop, FlowCanvas, FlowCard, FlowPopup
from page import page_part

from faceless_champ import (
    Animation,
    Bounds,
    Canvas,
    FlowDesign,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowPort,
    FlowScript,
    smooth,
)

DESIGN = FlowDesign.named("networking")
FONT, PALETTE = DESIGN.font, DESIGN.palette
TITLE = "Networking Explained"
DESIGN_VERSION = 2
TOTAL_DURATION = 120.0
CANVAS_SIZE = (1920, 1080)
VIEWPORT = (1728, 888)
DIAGRAM_BOUNDS = Bounds(96, 96, 1824, 984)
OFFSET = (96, 96)
CHAPTERS = (
    ("website", 0.0, 14.0),
    ("home-network", 14.0, 28.0),
    ("dns", 28.0, 46.0),
    ("internet-route", 46.0, 62.0),
    ("connection", 62.0, 78.0),
    ("request-response", 78.0, 94.0),
    ("page-packets", 94.0, 110.0),
    ("replay", 110.0, 116.0),
    ("complete", 116.0, 120.0),
)
STORYBOARD_TIMES = (8, 16.6, 22, 34.5, 40, 48.7, 55.5, 65.5, 73, 81, 87.5, 99, 106, 118)
PORTS = tuple(FlowPort(side, side) for side in ("left", "right", "top", "bottom", "center"))
LOCAL_PATH = ("wifi",)
DNS_PATH = ("wifi", "uplink", "dns-link")
WEB_PATH = ("wifi", "uplink", "backbone", "origin")
HERO_CENTER = (864.0, 430.0)
HERO_SCALE = 1.18
NODES = {
    "laptop": {
        "position": (240, 450),
        "size": (400, 430),
        "label": "Laptop",
        "icon": "laptop_icon",
        "detail": "192.168.1.20",
    },
    "router": {
        "position": (650, 450),
        "size": (200, 240),
        "label": "Wi-Fi router",
        "icon": "router_icon",
        "detail": "192.168.1.1",
    },
    "isp": {"position": (920, 450), "size": (180, 220), "label": "ISP", "icon": "internet_icon", "detail": None},
    "dns": {"position": (1120, 140), "size": (260, 180), "label": "DNS", "icon": "dns_icon", "detail": None},
    "hop": {"position": (1170, 570), "size": (180, 220), "label": "Internet", "icon": "cloud_icon", "detail": None},
    "server": {
        "position": (1510, 450),
        "size": (260, 340),
        "label": "Web server",
        "icon": "server_icon",
        "detail": "203.0.113.10",
    },
}
CARD_EVENTS = (
    ("laptop", 0.5, 120.0, 1.1),
    ("router", 16.0, 120.0, 1.0),
    ("isp", 28.2, 120.0, 0.95),
    ("dns", 30.2, 45.8, 0.95),
    ("hop", 46.0, 120.0, 1.0),
    ("server", 48.2, 120.0, 1.0),
    ("dns", 110.0, 120.0, 0.8),
)
POPUPS = (
    ("dns-query", (650, 120), "DNS", "example.com", 32.3, 36.7),
    ("dns-answer", (650, 120), "DNS", "203.0.113.10", 37.4, 43.0),
    ("tcp-syn", (1020, 120), "TCP", "SYN", 62.0, 64.6),
    ("tcp-syn-ack", (1020, 120), "TCP", "SYN-ACK", 64.6, 66.9),
    ("tcp-ack", (1020, 120), "TCP", "ACK", 66.9, 69.0),
    ("tls", (1020, 120), "TLS", "HTTPS :443", 69.7, 77.0),
    ("get", (1020, 120), "HTTPS", "GET /", 78.4, 84.0),
    ("status", (1020, 120), "HTTPS", "200 OK", 85.0, 92.0),
)


def world(position):
    return tuple(a + b for a, b in zip(position, OFFSET))


def build_diagram():
    """Public FlowChamp is the authority for every port, cable and packet route."""
    graph = FlowGraph(
        tuple(
            FlowNode(id, "", "rounded_rectangle", item["position"], item["size"], PORTS) for id, item in NODES.items()
        ),
        (
            FlowEdge("wifi", "laptop", "router", "right", "center", route="bezier", arrows="none"),
            FlowEdge("uplink", "router", "isp", "center", "center", route="bezier", arrows="none"),
            FlowEdge("dns-link", "isp", "dns", "center", "left", route="bezier", arrows="none"),
            FlowEdge("backbone", "isp", "hop", "center", "center", route="bezier", arrows="none"),
            FlowEdge("origin", "hop", "server", "center", "left", route="bezier", arrows="none"),
        ),
        layout="manual",
    )
    script = FlowScript()
    report = {"title": TITLE, "design_version": DESIGN_VERSION, "moves": [], "pops": [], "traffic": []}
    # Invisible proxies have no stroke. Only edges receive persistent color;
    # visible asset cards are ordinary core components above the cables.

    # Stage the hidden laptop for its opening hero pose. Initial graph positions
    # stay in the settled layout so static layout validation remains meaningful.
    script.move("laptop", HERO_CENTER, at=0, duration=0.001)
    script.scale("laptop", HERO_SCALE, at=0, duration=0.001)
    for id, at, end, duration in CARD_EVENTS:
        position = HERO_CENTER if id == "laptop" else NODES[id]["position"]
        scale = HERO_SCALE if id == "laptop" else 1.0
        frames = DESIGN.pop_frames(position, scale, duration)
        script.move(id, frames[0][1], at=at - 0.001, duration=0.001)
        script.scale(id, frames[0][2], at=at - 0.001, duration=0.001)
        script.reveal(id, at=at, duration=0.3)
        DESIGN.apply_transform(script, id, frames, at=at, duration=duration)
        report["pops"].append({"target": id, "start": at, "end": at + duration})
        if end < TOTAL_DURATION:
            script.hide(id, at=end - 0.5, duration=0.5)

    frames = DESIGN.move_frames(HERO_CENTER, NODES["laptop"]["position"], HERO_SCALE, 1.0, 2.35)
    DESIGN.apply_transform(script, "laptop", frames, at=14.0, duration=2.35)
    report["moves"].append(
        {
            "target": "laptop",
            "start": 14.0,
            "end": 16.35,
            "source": HERO_CENTER,
            "destination": NODES["laptop"]["position"],
        }
    )

    for id, at, duration in (
        ("wifi", 16.15, 1.85),
        ("uplink", 29.2, 1.1),
        ("dns-link", 30.5, 1.55),
        ("backbone", 47.25, 1.0),
        ("origin", 48.7, 1.9),
    ):
        script.draw(id, at=at, duration=duration, tool="none")
    script.hide("dns-link", at=45.3, duration=0.5)
    script.reveal("dns-link", at=110.0, duration=0.8)

    def traffic(id, path, at, duration, direction="forward", color=None):
        color = color or (PALETTE["teal"] if direction == "reverse" else PALETTE["blue"])
        DESIGN.signal(script, path, at=at, duration=duration, direction=direction, color=color)
        report["traffic"].append(
            {
                "id": id,
                "edges": path,
                "direction": direction,
                "start": at,
                "end": at + duration,
                "repeat": 1,
                "color": color,
            }
        )

    traffic("local-out", LOCAL_PATH, 20.0, 2.2)
    traffic("local-back", LOCAL_PATH, 23.4, 2.2, "reverse")
    traffic("dns-query", DNS_PATH, 32.8, 3.5, color=PALETTE["violet"])
    traffic("dns-answer", DNS_PATH, 38.0, 3.5, "reverse", PALETTE["violet"])
    traffic("route-out", WEB_PATH, 54.0, 3.0)
    traffic("route-back", WEB_PATH, 58.0, 3.0, "reverse")
    traffic("tcp-syn", WEB_PATH, 62.5, 1.9)
    traffic("tcp-syn-ack", WEB_PATH, 64.8, 1.9, "reverse")
    traffic("tcp-ack", WEB_PATH, 67.1, 1.4)
    traffic("tls-client", WEB_PATH, 70.2, 1.7, color=PALETTE["teal"])
    traffic("tls-server", WEB_PATH, 72.2, 1.7, "reverse")
    traffic("tls-ready", WEB_PATH, 74.2, 1.5, color=PALETTE["teal"])
    traffic("get", WEB_PATH, 79.5, 3.0)
    traffic("status", WEB_PATH, 86.0, 3.0, "reverse")
    for index, at in enumerate((94.5, 98.0, 101.5, 105.0), 1):
        traffic(f"page-{index}", WEB_PATH, at, 2.2, "reverse")
    traffic("recap-request", WEB_PATH, 110.1, 2.5)
    traffic("recap-response", WEB_PATH, 112.9, 2.5, "reverse")
    DESIGN.complete_connections(script, graph.edges, TOTAL_DURATION)
    return graph, script, report


def build(ctx):
    """Build the complete silent film; no image/video export occurs here."""
    ctx.canvas = Canvas(*CANVAS_SIZE, PALETTE["background"])
    ctx.safe_margin, ctx.caption_space, ctx.captions = 96, 0, False
    ctx.theme = replace(
        ctx.theme,
        name="networking-premium-v2",
        background=PALETTE["background"],
        surface=PALETTE["surface"],
        foreground=PALETTE["ink"],
        muted=PALETTE["muted"],
        accent=PALETTE["blue"],
        font=FONT,
        body_size=30,
        minimum_font_size=24,
        default_enter=None,
        default_exit=None,
        background_pattern=None,
    )
    video = Video(ctx)
    segment = video.segment("networking-explained", duration=TOTAL_DURATION)
    graph, script, _ = build_diagram()

    def add(id, factory, start=0, end=TOTAL_DURATION, *, z=4, bounds=DIAGRAM_BOUNDS):
        return segment.add_core(
            factory, id=id, bounds=bounds, at=start, duration=end - start, enter=None, exit=None, z_index=z
        )

    def background(context, bounds):
        result = FlowBackdrop(DESIGN).compose(context, bounds)
        result.root.training_id = "backdrop"
        return result

    add("backdrop", background, z=-10, bounds=Bounds(0, 0, *CANVAS_SIZE))

    def connections(context, bounds):
        result = FlowCanvas(graph, script, viewport=VIEWPORT, design=DESIGN).compose(context, bounds)
        result.root.training_id = "connections"
        result.children["diagram"].training_id = "connections"
        result.children["glow"].training_id = "connection-glow"
        return result

    add("connections", connections, z=-1)

    client_handle = None
    for index, (id, start, end, duration) in enumerate(CARD_EVENTS):
        spec = NODES[id]
        position = HERO_CENTER if id == "laptop" else spec["position"]
        scale = HERO_SCALE if id == "laptop" else 1.0

        def factory(context, bounds, id=id, spec=spec, position=position, scale=scale):
            cx, cy = world(position)
            width, height = spec["size"]
            pad = DESIGN.shadow_padding
            slot = Bounds(cx - width / 2 - pad, cy - height / 2 - pad, cx + width / 2 + pad, cy + height / 2 + pad)
            result = FlowCard(
                spec["label"],
                spec["icon"],
                spec["size"],
                detail=spec["detail"],
                address="example.com" if id == "laptop" else None,
                design=DESIGN,
            ).compose(context, slot)
            result.root.training_id = f"card-{id}"
            result.root.scale = scale
            return result

        handle = add(f"card-{id}-{index}", factory, start, end)
        frames = DESIGN.pop_frames(position, scale, duration)
        segment.play(
            handle,
            lambda component, f=frames: DESIGN.transform_animation(component, f, offset=OFFSET),
            at=start,
            duration=duration,
        )
        segment.play(
            handle,
            lambda component: Animation(component, {"opacity": 1}, {"opacity": 0}, rate_func=smooth),
            at=start,
            duration=0.36,
        )
        if end < TOTAL_DURATION:
            segment.play(handle, lambda component: component.animate.opacity_to(0), at=end - 0.5, duration=0.5)
        if id == "laptop":
            client_handle = handle
            frames = DESIGN.move_frames(HERO_CENTER, spec["position"], HERO_SCALE, 1.0, 2.35)
            segment.play(
                handle,
                lambda component, f=frames: DESIGN.transform_animation(component, f, offset=OFFSET),
                at=14,
                duration=2.35,
            )

    for id, center, kind, value, start, end in POPUPS:

        def popup_factory(context, bounds, id=id, center=center, kind=kind, value=value):
            cx, cy = world(center)
            result = FlowPopup(kind, value, design=DESIGN).compose(
                context, Bounds(cx - 308, cy - 116, cx + 308, cy + 116)
            )
            result.root.training_id = f"popup-{id}"
            return result

        handle = add(f"popup-{id}", popup_factory, start, end, z=8)
        frames = DESIGN.pop_frames(center, 1.0, 0.85)
        segment.play(
            handle,
            lambda component, f=frames: DESIGN.transform_animation(component, f, offset=OFFSET),
            at=start,
            duration=0.85,
        )
        segment.play(
            handle,
            lambda component: Animation(component, {"opacity": 1}, {"opacity": 0}, rate_func=smooth),
            at=start,
            duration=0.3,
        )
        segment.play(
            handle,
            lambda component: Animation(component, {"scale": 0.97, "opacity": 0}, rate_func=smooth),
            at=end - 0.35,
            duration=0.35,
        )

    # Browser output appears after the returning packets arrive. Each piece uses
    # the client's settled coordinate system and generous rounding.
    if client_handle is None:
        raise ValueError("Missing laptop card")
    segment.play(client_handle["icon"], lambda component: component.animate.opacity_to(0), at=94.0, duration=0.8)
    for id, start in (
        ("page-surface", 94.2),
        ("page-header", 96.7),
        ("page-image", 100.2),
        ("page-rows", 103.7),
        ("page-ready", 107.2),
    ):
        handle = add(id, lambda c, b, id=id: page_part(id, world(NODES["laptop"]["position"])), start, z=6)
        segment.play(
            handle,
            lambda component: Animation(
                component, {"opacity": 1, "scale": 1}, starts={"opacity": 0, "scale": 0.96}, rate_func=smooth
            ),
            at=start,
            duration=0.5,
        )
    return video
