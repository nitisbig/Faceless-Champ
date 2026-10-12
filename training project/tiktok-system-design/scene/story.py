"""Narration-specific graphs and cues; rendering and diagnostics belong to the libraries."""

from dataclasses import replace

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas

from faceless_champ import (
    Canvas,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowPort,
    FlowScript,
    Group,
    Polyline,
    ProgressBar,
    Rectangle,
    Text,
)

VIEWPORT = (1728, 888)
INK, MUTED, ACCENT = "#F4F3EE", "#B1ADA1", "#C15F3C"
CHAPTERS = (
    ("hook", None, 36),
    ("stages", 36, 63),
    ("upload", 63, 109),
    ("processing", 109, 162),
    ("delivery", 162, 246),
    ("recommendations", 246, 297),
    ("events", 297, 337),
    ("scaling", 337, 369),
    ("together", 369, None),
)


def node(id, label, x, y, symbol="service", size=(250, 130)):
    if label == "Recommendations":
        size = (340, size[1])
    return FlowNode(
        id,
        label,
        symbol,
        position=(x, y),
        size=size,
        ports=tuple(FlowPort(side, side) for side in ("left", "right", "top", "bottom")),
    )


def edge(id, source, target, source_port="right", target_port="left", **kwargs):
    return FlowEdge(id, source, target, source_port, target_port, **kwargs)


def diagram(segment, nodes, edges, events):
    """Apply authored actions at original word cues in this segment."""
    script = FlowScript()
    for kind, targets, cue, duration, options in events:
        at = 0 if cue is None else segment.cue_time(cue)
        getattr(script, kind)(targets, at=at, duration=duration, **options)
        if kind == "signal":
            script.highlight(targets, at=at, duration=duration, color=ACCENT)
    segment.add(FlowCanvas(FlowGraph(tuple(nodes), tuple(edges), layout="manual"), script, viewport=VIEWPORT))


def draw(targets, cue=None, duration=0.5, **options):
    return "draw", targets, cue, duration, {"tool": "none", **options}


def signal(targets, cue, duration=1.2, **options):
    return "signal", targets, cue, duration, {"marker": "packet", **options}


def highlight(targets, cue, duration=1.2, **options):
    return "highlight", targets, cue, duration, options


def hook(s):
    phones = [node("phone", "", 864, 400, size=(280, 510))]
    phones += [
        node(f"viewer{i}", "", x, y, size=(110, 184))
        for i, (x, y) in enumerate(
            ((280, 230), (550, 220), (1180, 220), (1450, 230), (280, 610), (550, 650), (1180, 650), (1450, 610))
        )
    ]
    diagram(
        s,
        phones,
        [],
        [
            draw("phone", 2, 0.45),
            draw([f"viewer{i}" for i in range(8)], 15, 0.4, stagger=0.14),
            highlight("phone", 22, 1.8),
        ],
    )

    def video_card(label):
        def factory(ctx, bounds):
            cx, cy = bounds.center[0], bounds.top + 400
            card = Rectangle(
                width=234,
                height=350,
                corner_radius=16,
                fill="#000000",
                stroke=ACCENT,
                stroke_width=3,
                position=(cx, cy),
            )
            play = Polyline(
                ((-23, -32), (31, 0), (-23, 32)), closed=True, fill=ACCENT, stroke=ACCENT, position=(cx, cy - 12)
            )
            text = Text(label, font_size=30, color=INK, position=(cx, cy + 105))
            return Group(card, play, text)

        return factory

    first = s.add_core(
        video_card("01"),
        id="first-video",
        at=s.cue_time(6),
        duration=s.cue_time(11) - s.cue_time(6),
        enter="fade",
        enter_duration=0.3,
        z_index=2,
    )
    s.play(first, lambda c: c.animate.move_to(c.position[0], c.position[1] - 70), at=s.cue_time(9), duration=0.45)
    s.play(first, lambda c: c.animate.opacity_to(0), at=s.cue_time(9), duration=s.cue_time(11) - s.cue_time(9))
    s.add_core(video_card("02"), id="next-video", at=s.cue_time(11), enter="fade", enter_duration=0.3, z_index=2)

    def playback(ctx, bounds):
        return ProgressBar(
            width=210,
            height=5,
            color=ACCENT,
            track_color=MUTED,
            progress=0,
            position=(bounds.center[0], bounds.top + 620),
        )

    bar = s.add_core(playback, id="playback", at=s.cue_time(6), z_index=3)
    s.play(bar, lambda c: c.animate.progress_to(1), at=s.cue_time(6), duration=1.5)


def stages(s):
    nodes = [
        node("video", "Video", 864, 150, "document", (160, 100)),
        node("upload", "Upload", 220, 390),
        node("process", "Processing", 650, 390),
        node("deliver", "Delivery", 1080, 390),
        node("recommend", "Recommendations", 1510, 390),
    ]
    edges = [
        edge("up", "upload", "process"),
        edge("out", "process", "deliver"),
        edge("rank", "recommend", "deliver", "left", "right"),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("video"),
            draw("upload", 46),
            draw("process", 48),
            draw("up", 49),
            draw("deliver", 50),
            draw("out", 51),
            draw("recommend", 54),
            draw("rank", 55),
            ("move", "video", 59, 0.5, {"position": (220, 150)}),
            signal(["up", "out"], 59, 1.3),
            highlight(["upload", "process", "deliver"], 59, 1.3),
        ],
    )


def upload(s):
    nodes = [
        node("creator", "Creator", 180, 420, "client", (170, 130)),
        node("gateway", "API gateway", 545, 420),
        node("upload", "Upload service", 950, 420),
        node("auth", "Authentication", 545, 180, size=(280, 100)),
        node("storage", "Object storage", 1480, 260, "database", (210, 130)),
        node("metadata", "Metadata", 1480, 600, "database", (210, 130)),
    ]
    edges = [
        edge("request", "creator", "gateway"),
        edge("route", "gateway", "upload"),
        edge("check", "gateway", "auth", "top", "bottom"),
        edge("bytes", "upload", "storage", waypoints=((1190, 420), (1190, 260))),
        edge("details", "upload", "metadata", waypoints=((1190, 420), (1190, 600))),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("creator"),
            highlight("creator", 65, 0.5),
            draw("gateway", 75),
            draw("request", 75),
            signal("request", 76),
            draw("auth", 79),
            draw("check", 79),
            signal("check", 79, 0.9),
            draw("upload", 86),
            draw("route", 86),
            signal("route", 87, 0.9),
            draw("storage", 93),
            draw("bytes", 93),
            signal("bytes", 94, 1.3),
            draw("metadata", 107),
            draw("details", 107),
            signal("details", 108, 0.6),
        ],
    )
    fields = s.add_core(
        lambda ctx, b: Text(
            "creator · caption · status", font_size=30, color=MUTED, position=(b.left + 1290, b.top + 790)
        ),
        at=s.cue_time(99),
        enter="fade",
        enter_duration=0.35,
        z_index=2,
    )
    s.play(fields, lambda c: c.animate.color_to(INK), at=s.cue_time(103), duration=0.35)


def processing(s):
    nodes = [
        node("raw", "Raw video", 220, 185, "database", (180, 110)),
        node("upload", "Upload service", 220, 490),
        node("queue", "Job queue", 630, 490, "queue", (240, 110)),
        node("workers", "Workers", 1030, 490, "server", (190, 140)),
        node("resolutions", "360p · 720p · 1080p", 1480, 170, size=(340, 110)),
        node("thumb", "Thumbnail", 1480, 420),
        node("safe", "Safety checks", 1480, 670),
    ]
    edges = [
        edge("enqueue", "upload", "queue"),
        edge("work", "queue", "workers"),
        edge("read", "raw", "workers", "right", "top", waypoints=((1030, 185),)),
        edge("encode", "workers", "resolutions", waypoints=((1260, 490), (1260, 170))),
        edge("thumbnail", "workers", "thumb", waypoints=((1260, 490), (1260, 420))),
        edge("moderate", "workers", "safe", waypoints=((1260, 490), (1260, 670))),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("raw"),
            highlight("raw", 111, 0.5),
            draw("upload", 120),
            draw("queue", 124),
            draw("enqueue", 127),
            signal("enqueue", 128),
            draw("workers", 130),
            draw("work", 130),
            signal("work", 131),
            draw("read", 134),
            signal("read", 134, 1.3),
            draw("resolutions", 139),
            draw("encode", 139),
            signal("encode", 139, 1.1),
            draw("thumb", 141),
            draw("thumbnail", 141),
            signal("thumbnail", 141, 0.8),
            draw("safe", 144),
            draw("moderate", 144),
            signal("moderate", 145, 0.7),
            highlight("queue", 151, 2.5),
            signal("enqueue", 155, 2.3, repeat=5),
            signal("work", 155, 2.3, repeat=2),
        ],
    )


def delivery(s):
    nodes = [
        node("viewer", "Viewer", 230, 465, "client", (180, 140)),
        node("feed", "Feed service", 760, 180),
        node("metadata", "Metadata", 1390, 180, "database", (210, 130)),
        node("cdn", "Nearby CDN", 1390, 570, "server", (210, 150)),
        node("current", "Playing", 710, 650, size=(250, 110)),
        node("next", "Next · ready", 710, 790, size=(250, 85)),
    ]
    edges = [
        edge("ask", "viewer", "feed", "top", "left", waypoints=((230, 180),)),
        edge("lookup", "feed", "metadata"),
        edge(
            "ids",
            "feed",
            "viewer",
            "bottom",
            "right",
            waypoints=((760, 400), (400, 400), (400, 465)),
            label="Video IDs",
        ),
        edge("play", "cdn", "current", "left", "right", waypoints=((1080, 570), (1080, 650)), label="Video bytes"),
        edge("preload", "cdn", "next", "bottom", "right", waypoints=((1390, 790),), dashed=True),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("viewer"),
            highlight("viewer", 164, 0.5),
            draw("feed", 179),
            draw("ask", 179),
            signal("ask", 180),
            draw("ids", 181),
            signal("ids", 183, 1.7),
            draw("metadata", 184),
            draw("lookup", 185),
            signal("lookup", 185),
            highlight("metadata", 197, 0.85),
            draw("cdn", 203),
            draw("current", 199),
            draw("play", 207),
            signal("play", 209, 4.0, repeat=3),
            highlight("cdn", 218, 2.4),
            signal("play", 222, 2.0, repeat=2),
            draw("next", 228),
            draw("preload", 228),
            signal("preload", 230, 1.6),
            highlight("next", 234, 1.5),
            highlight(["current", "next"], 241, 2.5),
            signal("play", 241, 2.5, repeat=3),
        ],
    )


def recommendations(s):
    nodes = [
        node("candidates", "Candidates", 250, 360, size=(300, 160)),
        node("rank", "Rank", 865, 360, size=(300, 160)),
        node("feed", "For You", 1470, 360, size=(280, 160)),
    ]
    signals = (
        ("watch", "Watch time", 270, 180),
        ("likes", "Likes", 272, 505),
        ("skips", "Skips", 273, 865),
        ("shares", "Shares", 274, 1225),
        ("features", "Video features", 279, 1550),
    )
    nodes += [node(id, label, x, 710, size=(240, 110)) for id, label, _, x in signals]
    edges = [edge("retrieve", "candidates", "rank"), edge("ranked", "rank", "feed")]
    # Each feature reaches a distinct rank port to keep the fan-in readable.
    rank = nodes[1]
    nodes[1] = replace(
        rank, ports=rank.ports + tuple(FlowPort(f"feature{i}", "bottom", 0.12 + i * 0.19) for i in range(5))
    )
    edges += [
        edge(f"in-{id}", id, "rank", "top", f"feature{i}", waypoints=((x, 560), (865 - 114 + i * 57, 560)))
        for i, (id, _, _, x) in enumerate(signals)
    ]
    events = [
        draw("feed"),
        highlight("feed", 251, 1.3),
        draw("candidates", 262),
        draw("rank", 265),
        draw("retrieve", 265),
        signal("retrieve", 265, 1.2),
        draw("ranked", 268),
        signal("ranked", 268, 1.2),
    ]
    for id, _, cue, _ in signals:
        events += [draw(id, cue), draw(f"in-{id}", cue), signal(f"in-{id}", cue, 0.75)]
    events += [highlight([id for id, *_ in signals], 285, 1.8)]
    diagram(s, nodes, edges, events)
    s.add_core(
        lambda ctx, b: Text("Illustrative architecture", font_size=30, color=MUTED, position=(b.center[0], b.top + 65)),
        at=s.cue_time(290),
        enter="fade",
        enter_duration=0.4,
        z_index=2,
    )


def events(s):
    nodes = [
        node("viewer", "Viewer", 180, 370, "client", (160, 120)),
        node("pipeline", "Event stream", 595, 370, "queue", (250, 110)),
        node("analytics", "Analytics", 1020, 180),
        node("features", "Interest features", 1020, 560, size=(290, 130)),
        node("recommend", "Recommendations", 1490, 560, size=(280, 130)),
        node("social", "Likes / comments", 580, 730, size=(290, 110)),
    ]
    edges = [
        edge("swipe", "viewer", "pipeline"),
        edge("measure", "pipeline", "analytics", waypoints=((800, 370), (800, 180))),
        edge("update", "pipeline", "features", waypoints=((800, 370), (800, 560))),
        edge("fresh", "features", "recommend"),
        edge("social-request", "viewer", "social", "bottom", "left", waypoints=((180, 730),)),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("viewer", 298),
            draw("pipeline", 305),
            draw("swipe", 305),
            signal("swipe", 307),
            draw("analytics", 309),
            draw("measure", 309),
            signal("measure", 309),
            draw("features", 312),
            draw("update", 313),
            signal("update", 313),
            draw("recommend", 317),
            draw("fresh", 321),
            signal("fresh", 321, 0.8),
            draw("social", 322),
            draw("social-request", 324),
            signal("social-request", 329, 1.1),
            highlight("social", 330, 1.4),
            signal("swipe", 332, 0.9),
        ],
    )


def scaling(s):
    nodes = [
        node("balance", "Load balancer", 240, 330),
        node("api1", "API 1", 670, 130, "server", (150, 90)),
        node("api2", "API 2", 670, 335, "server", (150, 90)),
        node("api3", "API 3", 670, 540, "server", (150, 90)),
        node("cache", "Cache", 1090, 330),
        node("metadata", "Metadata", 1510, 330, "database", (180, 110)),
        node("worker1", "Worker 1", 350, 750, "server", (140, 85)),
        node("worker2", "Worker 2", 640, 750, "server", (140, 85)),
        node("worker3", "Worker 3", 930, 750, "server", (140, 85)),
        node("cdn", "CDN", 1440, 750, "server", (220, 110)),
    ]
    edges = [
        edge(f"spread{i}", "balance", f"api{i}", waypoints=((460, 330), (460, y)))
        for i, y in ((1, 130), (2, 335), (3, 540))
    ]
    edges += [edge("cached", "api2", "cache"), edge("miss", "cache", "metadata", dashed=True)]
    diagram(
        s,
        nodes,
        edges,
        [
            draw("balance"),
            highlight("balance", 342, 0.5),
            draw(["api1", "api2", "api3"], 345, 0.4, stagger=0.15),
            draw(["spread1", "spread2", "spread3"], 345, 0.5),
            signal("spread1", 346, 0.65),
            signal("spread2", 347, 0.6),
            signal("spread3", 348, 0.65),
            draw("cache", 348),
            draw("cached", 348),
            signal("cached", 349, 1.1),
            draw("metadata", 351),
            draw("miss", 351),
            highlight("cache", 352, 0.6),
            draw("worker1", 353),
            draw(["worker2", "worker3"], 355, 0.4, stagger=0.25),
            highlight(["worker1", "worker2", "worker3"], 359, 0.6),
            draw("cdn", 361),
            highlight("cdn", 363, 1.5),
        ],
    )


def together(s):
    motion_end = s.cue_time(399, edge="end")
    nodes = [
        node("creator", "Creator", 145, 245, "client", (170, 100)),
        node("gateway", "Gateway", 510, 245),
        node("upload", "Upload", 905, 245),
        node("storage", "Storage", 1450, 245, "database", (190, 120)),
        node("queue", "Queue", 905, 490, "queue", (190, 95)),
        node("workers", "Workers", 1450, 490, "server", (180, 110)),
        node("viewer", "Viewer", 145, 720, "client", (130, 100)),
        node("feed", "Feed", 510, 720),
        node("recommend", "Recommendations", 905, 720, size=(280, 130)),
        node("cdn", "CDN", 1450, 720, "server", (180, 110)),
    ]
    edges = [
        edge("request", "creator", "gateway"),
        edge("route", "gateway", "upload"),
        edge("bytes", "upload", "storage"),
        edge("enqueue", "upload", "queue", "bottom", "top"),
        edge("process", "queue", "workers"),
        edge("publish", "workers", "storage", "top", "bottom"),
        edge("ask", "viewer", "feed"),
        edge("rank", "recommend", "feed", "left", "right"),
        edge("deliver", "cdn", "viewer", "bottom", "bottom", waypoints=((1450, 850), (145, 850))),
        edge("edge-copy", "storage", "cdn", "right", "right", waypoints=((1620, 245), (1620, 720))),
    ]
    diagram(
        s,
        nodes,
        edges,
        [
            draw([n.id for n in nodes], None, 0.6),
            draw([e.id for e in edges], 377, 0.65),
            highlight(["gateway", "feed"], 385, 0.35),
            highlight("queue", 387, 0.5),
            signal(["request", "route", "bytes"], 390, motion_end - s.cue_time(390), repeat=2),
            signal("rank", 391, motion_end - s.cue_time(391), repeat=2),
            signal("deliver", 393, motion_end - s.cue_time(393), repeat=2),
        ],
    )


AUTHORS = (hook, stages, upload, processing, delivery, recommendations, events, scaling, together)


def build(ctx):
    ctx.canvas = Canvas(1920, 1080, "#000000")
    ctx.theme = replace(
        ctx.theme,
        name="terracotta",
        background="#000000",
        surface="#000000",
        foreground=INK,
        muted=MUTED,
        accent=ACCENT,
        body_size=38,
        minimum_font_size=28,
    )
    ctx.captions = False
    video = Video(ctx)
    narration = video.narration(
        audio="audio.mp3", subtitles="cue-per-word.srt", captions=False, overlap_tolerance=0.001
    )
    for (name, first, next), author in zip(CHAPTERS, AUTHORS):
        start = narration.track.cue(first).start if first else 0
        end = narration.track.cue(next).start if next else narration.duration
        segment = video.segment(name, start=start, duration=end - start)
        author(segment)
    return video
