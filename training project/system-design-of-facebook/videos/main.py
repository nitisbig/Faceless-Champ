"""Authored graphs and timing only; all geometry/playback live in core and Kit."""

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas

from faceless_champ import (
    Bounds,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowPort,
    FlowScript,
    FlowTheme,
    ProgressBar,
    Rectangle,
    ShadowStyle,
    card_surface,
    fit_text,
)

TOTAL_DURATION = 32.0
OVERLAP = 0.6
VIEWPORT = (1210, 500)
ORANGE = "#FF5A20"
INK = "#111111"
MUTED = "#737373"
NOMINAL_SCENES = (
    ("routing", 0, 8, "One request, many services."),
    ("publish", 8, 16, "Publish once. Process asynchronously."),
    ("feed", 16, 24, "Build a feed for each reader."),
    ("media", 24, 32, "Keep media near the reader."),
)
STORYBOARD_TIMES = (0.8, 3.5, 6.4, 7.85, 8.15, 11.5, 14.4, 15.85, 16.15, 19.5, 22.4, 23.85, 24.15, 27.5, 30.4, 31.5)


def scene_windows():
    return [
        {
            "id": id,
            "nominal_start": start,
            "nominal_end": end,
            "start": max(0, start - OVERLAP / 2),
            "end": min(TOTAL_DURATION, end + OVERLAP / 2),
            "title": title,
        }
        for id, start, end, title in NOMINAL_SCENES
    ]


def node(id, label, x, y, *, symbol="service", size=(200, 110)):
    return FlowNode(
        id,
        label,
        symbol,
        position=(x, y),
        size=size,
        ports=(
            FlowPort("left", "left"),
            FlowPort("right", "right"),
            FlowPort("top", "top"),
            FlowPort("bottom", "bottom"),
            FlowPort("upper", "right", 0.2),
            FlowPort("lower", "right", 0.8),
            FlowPort("in-upper", "left", 0.2),
            FlowPort("in-lower", "left", 0.8),
        ),
    )


def edge(id, source, target, label="", *, start="right", end="left", position=0.5, offset=(0, -30), **kwargs):
    return FlowEdge(id, source, target, start, end, label=label, label_position=position, label_offset=offset, **kwargs)


def reveal(graph):
    script = FlowScript().reveal([n.id for n in graph.nodes], at=0.65, duration=0.4, stagger=0.1)
    script.draw([e.id for e in graph.edges], at=1.6, duration=0.55, stagger=0.1, tool="none")
    return script


def routing():
    graph = FlowGraph(
        (
            node("client", "Client", 115, 225, symbol="client", size=(130, 145)),
            node("balance", "Load\nbalancer", 415, 225),
            node("api", "API", 725, 225, size=(190, 110)),
            node("feed", "Feed service", 1065, 105, size=(220, 105)),
            node("posts", "Post service", 1065, 350, size=(220, 105)),
        ),
        (
            edge("request", "client", "balance", "HTTPS", route="straight"),
            edge("route", "balance", "api", "route", route="straight"),
            edge("read", "api", "feed", "read", start="upper", position=0.72),
            edge("write", "api", "posts", "write", start="lower", position=0.72),
        ),
        layout="manual",
    )
    script = reveal(graph)
    script.signal(["request", "route", "read"], at=2.7, duration=1.9, marker="packet")
    script.highlight("feed", at=4.25, duration=0.55)
    script.signal(["request", "route", "read"], at=4.8, duration=0.8, direction="reverse", marker="packet")
    script.signal(["request", "route", "write"], at=5.7, duration=1.3, marker="packet")
    script.highlight("posts", at=6.7, duration=0.5)
    return graph, script


def publish():
    graph = FlowGraph(
        (
            node("api", "Post API", 110, 190, size=(170, 110)),
            node("store", "Post store", 415, 190, symbol="database", size=(150, 115)),
            node("queue", "Event queue", 735, 190, symbol="queue", size=(155, 115)),
            node("feed", "Feed worker", 1065, 100, size=(220, 105)),
            node("notify", "Notifications", 1065, 350, size=(220, 105)),
        ),
        (
            edge("commit", "api", "store", "commit", route="straight"),
            edge("event", "store", "queue", "event", route="straight"),
            edge("update", "queue", "feed", "update", start="upper", position=0.55),
            edge("notify-event", "queue", "notify", "notify", start="lower", position=0.72),
        ),
        layout="manual",
    )
    script = reveal(graph)
    script.signal("commit", at=2.7, duration=0.65, marker="packet")
    script.highlight("store", at=3.25, duration=0.45)
    script.signal("event", at=3.75, duration=0.65, marker="packet")
    script.signal("update", at=4.55, duration=1.1, marker="packet")
    script.signal("notify-event", at=4.55, duration=1.1, marker="packet")
    script.highlight(["feed", "notify"], at=5.6, duration=0.7)
    script.signal("update", at=6.4, duration=0.8, marker="packet")
    return graph, script


def feed():
    graph = FlowGraph(
        (
            node("inventory", "Candidate\nposts", 150, 105, symbol="database", size=(170, 95)),
            node("graph", "Graph / cache", 150, 350, symbol="database", size=(180, 95)),
            node("aggregate", "Feed\naggregator", 540, 225, size=(220, 110)),
            node("rank", "Rank", 855, 225, size=(170, 110)),
            node("client", "Client", 1100, 225, symbol="client", size=(115, 140)),
        ),
        (
            edge("candidates", "inventory", "aggregate", "posts", end="in-upper", position=0.32),
            edge("features", "graph", "aggregate", "signals", end="in-lower", position=0.32, offset=(0, 30)),
            edge("score", "aggregate", "rank", "score", route="straight"),
            edge("result", "rank", "client", route="straight"),
        ),
        layout="manual",
    )
    script = reveal(graph)
    script.signal("candidates", at=2.7, duration=1.0, marker="packet")
    script.signal("features", at=2.7, duration=1.0, marker="packet")
    script.signal("score", at=3.8, duration=0.8, marker="packet")
    script.highlight("rank", at=4.6, duration=0.7)
    script.signal("result", at=5.4, duration=0.8, marker="packet")
    script.signal(["score", "result"], at=6.3, duration=0.9, marker="packet")
    return graph, script


def media():
    graph = FlowGraph(
        (
            node("upload", "Upload", 130, 215, symbol="client", size=(135, 145)),
            node("store", "Object store", 450, 215, symbol="database", size=(175, 120)),
            node("cdn", "CDN", 775, 215, size=(180, 110)),
            node("reader", "Reader", 1090, 215, symbol="client", size=(135, 145)),
        ),
        (
            edge("upload-bytes", "upload", "store", "upload", route="straight"),
            edge(
                "miss",
                "cdn",
                "store",
                "cache miss",
                start="top",
                end="top",
                route="straight",
                waypoints=((775, 50), (450, 50)),
                offset=(0, -14),
                dashed=True,
            ),
            edge("fill", "store", "cdn", "bytes", route="straight"),
            edge("deliver", "cdn", "reader", "deliver", route="straight"),
        ),
        layout="manual",
    )
    script = reveal(graph)
    script.signal("upload-bytes", at=2.7, duration=0.8, marker="packet")
    script.highlight("store", at=3.45, duration=0.45)
    script.signal("miss", at=3.95, duration=0.85, marker="packet")
    script.signal(["fill", "deliver"], at=4.85, duration=1.15, marker="packet")
    script.highlight("cdn", at=6.05, duration=0.4)
    script.signal("deliver", at=6.5, duration=0.7, marker="packet")
    return graph, script


BUILDERS = (routing, publish, feed, media)
NOTES = (
    ("ROUTE", "Separate the\nread and write\npaths.", "The API routes each request to the service that owns the work."),
    (
        "PUBLISH",
        "Commit first.\nWork in the\nbackground.",
        "A durable event queue decouples feed updates and notifications from the request.",
    ),
    (
        "PERSONALIZE",
        "Gather.\nScore.\nReturn.",
        "Collect eligible posts and graph signals, then rank a feed for this reader.",
    ),
    (
        "DELIVER",
        "Cache hits\nshorten the\npath.",
        "A miss fetches bytes from origin storage. Later requests reuse the CDN copy.",
    ),
)


def text(segment, id, value, box, *, size=34, weight=400, color=INK, **kwargs):
    return segment.add_core(
        lambda ctx, b: fit_text(
            value,
            b,
            font=ctx.theme.font,
            font_weight=weight,
            font_size=size,
            min_font_size=min(size, 26),
            color=color,
            align="left",
            spacing=4,
        ),
        id=id,
        bounds=box,
        **kwargs,
    )


def build(ctx):
    video = Video(ctx)
    with video.segment("chrome", duration=TOTAL_DURATION) as segment:
        text(segment, "title", "System design of Facebook", Bounds(110, 65, 1810, 155), size=72, weight=700)
        text(
            segment,
            "scope",
            "SIMPLIFIED TEACHING MODEL  /  SILENT TEST",
            Bounds(114, 166, 1800, 205),
            size=24,
            color=MUTED,
        )
        text(segment, "brand", "FLOWCHAMP", Bounds(112, 994, 430, 1035), size=24, weight=700, color=MUTED)
        text(segment, "duration", "00:32", Bounds(1710, 994, 1840, 1035), size=24, color=MUTED)
        for index, (_, start, end, _) in enumerate(NOMINAL_SCENES):
            x = 720 + index * 145
            h = segment.add_core(
                lambda ctx, b: ProgressBar(width=120, height=8, color=ORANGE, track_color="#CFCAC3", position=b.center),
                id=f"progress-{index}",
                bounds=Bounds(x, 1010, x + 120, 1018),
            )
            segment.play(h, lambda c: c.animate.progress_to(1), at=start + 0.65, duration=6.6)
    for index, (window, factory, note) in enumerate(zip(scene_windows(), BUILDERS, NOTES)):
        with video.segment(window["id"], start=window["start"], duration=window["end"] - window["start"]) as segment:
            for id, box in (("diagram-card", Bounds(50, 206, 1460, 972)), ("note-card", Bounds(1400, 206, 1905, 972))):
                segment.add_core(
                    lambda ctx, b: card_surface(b, fill="#FFFFFF", radius=44, shadow=ShadowStyle()), id=id, bounds=box
                )
            # Titles hand off at the nominal boundary, while card surfaces crossfade.
            title_timing = {
                "at": window["nominal_start"] - window["start"],
                "duration": 8,
                "enter_duration": 0.3,
                "exit_duration": 0.3,
                "z_index": 2,
            }
            text(
                segment, "view-title", window["title"], Bounds(154, 284, 1360, 343), size=43, weight=700, **title_timing
            )
            text(
                segment,
                "step",
                f"0{index + 1} / {note[0]}",
                Bounds(1493, 302, 1810, 345),
                size=25,
                weight=700,
                color=ORANGE,
                **title_timing,
            )
            text(segment, "takeaway", note[1], Bounds(1493, 379, 1810, 553), size=43, weight=700, **title_timing)
            segment.add_core(
                lambda ctx, b: Rectangle(width=300, height=2, position=b.center, fill="#E8E6E2", stroke=None),
                id="divider",
                bounds=Bounds(1493, 574, 1810, 598),
                **title_timing,
            )
            text(segment, "explanation", note[2], Bounds(1493, 626, 1810, 842), size=31, **title_timing)
            graph, script = factory()
            segment.add(
                FlowCanvas(
                    graph,
                    script,
                    viewport=VIEWPORT,
                    theme=FlowTheme(
                        foreground=INK,
                        surface="#FFFFFF",
                        accent=ORANGE,
                        stroke=MUTED,
                        background="#FFFFFF",
                        font=ctx.theme.font,
                        font_size=34,
                        minimum_font_size=28,
                        stroke_width=3,
                    ),
                ),
                id="diagram",
                bounds=Bounds(150, 355, 1360, 855),
                z_index=1,
            )
            for placement in segment.placements:
                placement.z_index += (index + 1) * 100
    return video
