"""Narration-directed quickstart composed with Kit and core, without captions."""

import math

from facelesschamp_kit import Video

from faceless_champ import (
    Arrow,
    Bounds,
    Circle,
    CodeEditor,
    Draw,
    Group,
    Image,
    PlaygroundOutput,
    Polyline,
    Rectangle,
    Typewriter,
)

from .design import CODE_THEME, Artist, box, label
from .design import line as Line
from .playground import ExamplePlayback
from .spec import (
    ACCENT,
    INK,
    LINE,
    MUTED,
    PROJECT,
    ROOT,
    chapters,
    context,
    examples,
    lesson_scripts,
    require_audio,
    track,
)


def output(
    a,
    prepared,
    cue=None,
    *,
    until=None,
    keys=((0, 2),),
    only=(),
    checkpoint=-1,
    width=760,
    x=1432,
    y=448,
    source_start=0,
):
    height = width * 1080 / 1920
    a.put(box(x, y, width + 4, height + 4, fill="#000000", radius=4), cue, until=until)
    return a.put(
        ExamplePlayback(
            prepared,
            checkpoint=checkpoint,
            keys=keys,
            only=only,
            width=width,
            height=height,
            position=(x, y),
            source_start=source_start,
        ),
        cue,
        until=until,
        enter=False,
    )


def live_editor(a, prepared, cue=None, *, until=None, source_start=0, x=560, y=520, width=960, height=840):
    return a.put(
        CodeEditor(
            prepared.script,
            width=width,
            height=height,
            font_size=30,
            theme=CODE_THEME,
            position=(x, y),
            source_start=source_start,
        ),
        cue,
        until=until,
    )


def console(a, prepared, cue=None, *, until=None, source_start=0):
    return a.put(
        PlaygroundOutput(
            prepared, width=760, height=154, font_size=28, position=(1432, 816), source_start=source_start
        ),
        cue,
        until=until,
    )


def opening(a, ctx, assets):
    base = examples()["baseline"].splitlines()
    a.code("\n".join(base[12:28]), None, file="hello.py", first=12, h=820)
    # A mini replay then a quiet hold while the narration widens the idea.
    output(
        a, assets["author"], keys=((0, 0), (2.46, 0), (3.8, 1.5), (4.6, 3), (5.5, 4.5), (6.4, 5.3), (8, 5.8)), until=39
    )
    a.text("1920 × 1080", 1432, 720, 1, size=30, color=MUTED, until=39)
    a.flow(ctx, ("Python", "timeline", "MP4"), 39, bounds=Bounds(1100, 320, 1800, 500))
    for i, c in enumerate((48, 53, 60)):
        a.put(Circle(14, fill=ACCENT, stroke=None, position=(1210 + i * 190, 720)), c)
        a.text(("build", "render", "extend")[i], 1210 + i * 190, 775, c, size=30)


def model(a, ctx, assets):
    a.put(box(960, 520, 1360, 730, fill="#070809", stroke=LINE), 65)
    a.put(Group(box(570, 450, 250, 190), label("{ }", 570, 450, 76, color=ACCENT)), 65, until=90)
    a.put(Arrow((760, 450), (1130, 450), stroke=LINE, stroke_width=3, tip_size=16), 65, until=90)
    preview = a.put(Circle(50, fill=ACCENT, stroke=None, position=(1290, 450)), 65, until=90)
    a.motion(preview, lambda c: c.animate.move_to(1290, 530), 79, duration=1)
    a.text("Scene", 960, 202, 90, color=ACCENT)
    a.text("timeline", 960, 830, 101, size=30, color=MUTED)
    a.put(Line((370, 790), (1550, 790), stroke=LINE, stroke_width=3), 101)
    for i, x in enumerate((470, 800, 1130, 1460)):
        a.put(Line((x, 780), (x, 800), stroke=ACCENT, stroke_width=3), 101 + i)
    t = a.put(label("Text", 510, 420, 58), 110)
    a.motion(t, lambda c: Typewriter(c), 110, duration=0.65, offset=0.35)
    dot = a.put(Circle(48, fill=ACCENT, stroke=None, position=(800, 430)), 111)
    a.put(Image(ROOT / "assets/chess/white-knight.png", width=104, height=130, position=(1110, 425)), 112)
    chart = Group(
        Line((1370, 505), (1580, 505), stroke=LINE, stroke_width=2),
        Polyline([(1380, 480), (1430, 450), (1480, 462), (1530, 400), (1570, 350)], stroke=ACCENT, stroke_width=4),
    )
    a.put(chart, 113)
    a.text("components", 960, 632, 105, size=34, color=MUTED)
    a.motion(dot, lambda c: c.animate.move_to(900, 430), 127, duration=1)
    a.motion(t, lambda c: c.animate.opacity_to(0.25), 125, duration=0.6)
    a.motion(t, lambda c: c.animate.opacity_to(1), 131, duration=0.6)


def setup(a, ctx, assets):
    # The requirements turn into an environment, then make room for real commands.
    for cue, x, name, detail in (
        (140, 470, "Python", "3.12+"),
        (145, 960, "Git", "clone"),
        (147, 1450, "FFmpeg", "H.264"),
    ):
        a.put(box(x, 320, 410, 230), cue, until=168)
        a.text(name, x, 286, cue, size=44, until=168)
        a.text(detail, x, 370, cue, size=34, color=ACCENT, until=168)
    a.text("ffprobe", 1300, 535, 158, size=34, color=ACCENT, until=168)
    a.text("libx264", 1580, 535, 166, size=34, color=ACCENT, until=168)
    commands = [
        (168, "git clone https://github.com/nitisbig/Faceless-Champ.git", "clone"),
        (172, "cd Faceless-Champ", "folder"),
        (175, "python3 -m venv .venv", "environment"),
        (180, "source .venv/bin/activate", "activate"),
        (183, "python -m pip install -e .", "install"),
    ]
    stops = [172, 175, 180, 183, None]
    for i, ((cue, line, name), end) in enumerate(zip(commands, stops)):
        source = "\n".join(x[1] for x in commands[: i + 1])
        a.code(
            source,
            cue,
            until=end,
            x=960,
            y=475,
            w=1700,
            h=560,
            size=34,
            file="Terminal",
            language="bash",
            highlights=(i + 1,),
        )
    a.flow(ctx, (".venv", "Faceless Champ", "render"), 194, bounds=Bounds(330, 815, 1590, 960))


def author(a, ctx, assets):
    live_editor(a, assets["author"])
    a.text("hello.py", 1432, 215, 210, color=MUTED)
    a.put(box(1432, 470, 764, 430, fill="#000000", radius=4), 210, until=299)
    a.put(
        Rectangle(width=380, height=214, fill=None, stroke=LINE, stroke_width=2, position=(1432, 470)), 258, until=282
    )
    a.text("1920 × 1080", 1432, 770, 256, size=34, color=ACCENT, until=282)
    a.text("design pixels", 1432, 820, 265, size=30, color=MUTED, until=282)
    a.text("1280 × 720", 1432, 530, 267, size=30, color=MUTED, until=282)
    output(a, assets["author"], 299, only=("text",), keys=((0, 2),), y=470)
    console(a, assets["author"], 309, source_start=a.time(309) - a.cues.cue(210).start)


def coordinates(a, ctx, assets):
    # Focused enlargement uses the same prepared coordinates as the example.
    width = 1440
    left = 240
    top = 190
    scale = width / 1920
    output(a, assets["author"], only=("text",), width=width, x=960, y=595, keys=((0, 2),))
    ox, oy = left, top
    a.put(Circle(7, fill=ACCENT, stroke=None, position=(ox, oy)), 321)
    a.text("(0, 0)", ox + 60, oy - 42, 321, size=30, color=ACCENT)
    xarr = a.put(Arrow((ox + 12, oy), (ox + 430, oy), stroke=ACCENT, stroke_width=3, tip_size=13), 328)
    a.motion(xarr, lambda c: Draw(c), 328, duration=0.6, offset=0.35)
    a.text("x →", ox + 470, oy, 328, color=ACCENT)
    yarr = a.put(Arrow((ox, oy + 12), (ox, oy + 400), stroke="#89B4FA", stroke_width=3, tip_size=13), 334)
    a.motion(yarr, lambda c: Draw(c), 334, duration=0.6, offset=0.35)
    a.text("y ↓", ox + 55, oy + 425, 334, color="#89B4FA")
    tx, ty = left + 960 * scale, top + 400 * scale
    a.put(
        Group(
            Line((tx - 18, ty), (tx + 18, ty), stroke=ACCENT, stroke_width=3),
            Line((tx, ty - 18), (tx, ty + 18), stroke=ACCENT, stroke_width=3),
        ),
        342,
    )
    a.put(Line((tx, oy + 15), (tx, ty - 70), stroke=LINE, stroke_width=2), 354)
    a.text("960", tx + 70, oy + 75, 354, size=34, color=ACCENT)
    a.put(Line((ox + 15, ty), (tx - 420, ty), stroke=LINE, stroke_width=2), 357)
    a.text("400", ox + 65, ty - 55, 357, size=34, color="#89B4FA")
    a.text("(960, 400)", 960, 730, 354, size=38, color=ACCENT)
    a.text("center anchor", 960, 800, 342, size=32, color=MUTED)


def circle(a, ctx, assets):
    live_editor(a, assets["author"], source_start=a.segment.start - a.cues.cue(210).start)
    output(a, assets["author"], keys=((0, 2),))
    console(a, assets["author"], 379, source_start=a.time(379) - a.cues.cue(210).start)
    # Match the prepared circle's 60-pixel radius and initial position.
    sx, sy = 1432 - 380 + 400 * 760 / 1920, 448 - 213.75 + 700 * 760 / 1920
    a.put(Line((sx, sy), (sx + 60 * 760 / 1920, sy), stroke=INK, stroke_width=3), 369)
    a.text("r = 60", sx + 90, sy - 72, 369, size=34, color=ACCENT)
    a.text("(400, 700)", sx + 95, sy + 88, 377, size=34, color=MUTED)


def timeline(a, ctx, assets):
    start = a.segment.start
    at = lambda c: a.time(c) - start
    live_editor(a, assets["author"], source_start=start - a.cues.cue(210).start)
    # Freeze at explanatory poses; play actual library movement at the spoken action.
    output(
        a,
        assets["author"],
        keys=((0, 0), (at(401), 0), (at(412), 1.5), (at(453), 2), (at(461), 4), (at(509), 4.5), (at(517), 5.3)),
    )
    a.text("Typewriter", 1225, 724, 401, size=30, until=453)
    a.text("FadeIn", 1225, 800, 408, size=30, until=453)
    for cue, y, color in ((401, 716, ACCENT), (408, 792, "#89B4FA")):
        h = a.put(box(1590, y, 320, 30, fill=color, stroke=None, radius=6), cue, until=453)
        a.motion(h, lambda c: c.animate.height_to(18), 425, duration=0.5)
    a.text("1.5 s", 1590, 864, 434, size=34, color=ACCENT, until=453)
    a.text("wait(0.5)", 1432, 947, 441, size=34, color=MUTED, until=481)
    a.text("move_to(1520, 700)", 1432, 778, 453, size=30, color=ACCENT, until=481)
    a.text("run_time = 2", 1432, 850, 471, size=34, color=MUTED, until=481)
    a.flow(ctx, ("play", "wait", "play"), 481, bounds=Bounds(1100, 700, 1800, 845), until=509)
    a.text("sequence", 1432, 920, 481, size=32, color=MUTED, until=509)
    a.text("FadeOut", 1432, 812, 512, size=34, color=ACCENT)


def export(a, ctx, assets):
    commands = "faceless-champ render hello.py Hello \\\n    -o output/hello.mp4 \\\n    -q ql --antialias 1"
    a.code(commands, 524, x=960, y=296, w=1700, h=340, size=34, file="Terminal", language="bash", until=565)
    for cue, x, word in ((537, 420, "hello.py"), (541, 780, "Hello"), (546, 1300, "output/hello.mp4")):
        a.text(word, x, 575, cue, size=34, color=ACCENT, until=565)
    a.text("-q ql", 700, 712, 549, size=38, color=ACCENT, until=565)
    a.text("--antialias 1", 1200, 712, 559, size=38, color=MUTED, until=565)
    a.text("output/hello.mp4", 960, 145, 565, size=30, color=MUTED)
    output(
        a,
        assets["author"],
        565,
        width=1440,
        x=960,
        y=570,
        keys=((0, 0), (0.8, 0), (2.3, 1.5), (2.8, 2), (4.8, 4), (5.3, 4.5), (6.1, 5.3), (6.6, 5.8)),
    )


def edits(a, ctx, assets):
    live_editor(a, assets["edits"])
    output(a, assets["edits"], checkpoint=None, keys=((0, 2), (7.2, 2), (9.3, 2), (12.3, 4.3)))
    console(a, assets["edits"], source_start=0)
    a.text("--overwrite", 1432, 957, 601, size=34, color=ACCENT)
    # Explicitly connect the final edited source to its changed result.
    a.motion(
        a.put(Arrow((1065, 915), (1780, 915), stroke=LINE, stroke_width=2, tip_size=10), 611),
        lambda c: Draw(c),
        611,
        duration=0.6,
        offset=0.35,
    )


def narration(a, ctx, assets):
    source = 'self.add_audio("voiceover.mp3", start=0)\ntrack = SubtitleTrack.from_srt("words.srt")\nwith self.at(track.cue(12).start):\n    self.play(FadeIn(diagram))'
    a.code(source, 641, x=960, y=275, w=1700, h=320, size=32, file="narrated.py", until=676)
    a.put(Image(ROOT / "assets/chess/white-knight.png", width=115, height=130, position=(430, 465)), 635, until=641)
    a.text("Image", 430, 562, 635, size=32, until=641)
    # Original audio samples determine the waveform, not a decorative random curve.
    import array
    import wave

    with wave.open(str(PROJECT / ".fc-kit/narration.wav"), "rb") as wav:
        data = array.array("h", wav.readframes(wav.getnframes()))
    span = len(data) // 170
    envelope = []
    for i in range(170):
        chunk = data[i * span : (i + 1) * span]
        rms = math.sqrt(sum(v * v for v in chunk) / max(1, len(chunk))) / 32768
        envelope.append(rms)
    peak = max(envelope) or 1
    points = [(250 + i * 8.35, 660 + (-1 if i % 2 else 1) * 75 * rms / peak) for i, rms in enumerate(envelope)]
    a.put(Polyline(points, stroke=ACCENT, stroke_width=3), 637, until=676)
    a.put(Line((245, 770), (1690, 770), stroke=LINE, stroke_width=3), 639, until=676)
    a.text("0", 245, 816, 649, size=32, color=ACCENT, until=676)
    a.put(Line((245, 622), (245, 790), stroke=ACCENT, stroke_width=2), 649, until=676)
    marker = a.put(Line((1100, 600), (1100, 790), stroke="#F5C879", stroke_width=3), 660, until=676)
    a.text("cue 12", 1100, 820, 660, size=32, color="#F5C879", until=676)
    a.put(Group(box(1440, 510, 300, 140), label("diagram", 1440, 510, 36)), 669, until=676)
    a.motion(marker, lambda c: c.animate.opacity_to(0.45), 669, duration=0.6)
    # Three restrained, visual applications replace the code once its point is made.
    a.text("f(x) = x²", 455, 340, 682, size=46, color=ACCENT)
    curve = a.put(
        Polyline([(280 + i * 10, 700 - ((i - 17) / 17) ** 2 * 250) for i in range(35)], stroke=ACCENT, stroke_width=4),
        682,
    )
    a.motion(curve, lambda c: Draw(c), 682, duration=0.8, offset=0.35)
    a.code("for frame in timeline:\n    render(frame)", 684, x=980, y=535, w=470, h=300, size=28, file="lesson.py")
    a.flow(ctx, ("API", "queue", "worker"), 687, bounds=Bounds(1300, 400, 1810, 630))


def kit(a, ctx, assets):
    a.put(box(960, 310, 1300, 370, fill="#070809"), 696, until=716)
    a.text("core", 960, 413, 714, size=40, color=ACCENT, until=716)
    # Kit is a structure around the engine; add only the item currently introduced.
    for cue, x, word in ((700, 470, "segments"), (702, 800, "blocks"), (704, 1130, "theme"), (705, 1460, "assets")):
        a.put(box(x, 240, 260, 100), cue, until=716)
        a.text(word, x, 240, cue, size=32, until=716)
    a.text("Kit", 960, 563, 698, size=34, color=MUTED, until=716)
    setup = "python -m pip install -e ./facelesschamp-kit\nfc-kit init my-video --template silent\ncd my-video"
    a.code(setup, 716, x=960, y=270, w=1700, h=320, size=32, file="Terminal", language="bash", until=728)
    generated = (PROJECT / ".fc-kit/starter/videos/main.py").read_text()
    a.code(generated, 728, x=960, y=455, w=1760, h=750, size=30, file="videos/main.py", until=733)
    commands = [
        (733, "fc-kit doctor"),
        (739, "fc-kit validate main"),
        (745, "fc-kit preview main -o output/preview.mp4"),
        (756, "fc-kit render main -o output/main.mp4"),
    ]
    for i, (cue, command) in enumerate(commands):
        end = commands[i + 1][0] if i + 1 < len(commands) else None
        a.code(
            "\n".join(x[1] for x in commands[: i + 1]),
            cue,
            until=end,
            x=960,
            y=330,
            w=1700,
            h=440,
            size=32,
            file="Terminal",
            language="bash",
            highlights=(i + 1,),
        )
    a.flow(ctx, ("doctor", "validate", "preview", "render"), 733, bounds=Bounds(240, 725, 1680, 900))


def recap(a, ctx, assets):
    a.put(box(960, 530, 1440, 720, fill="#000000", radius=4), None, until=797)
    a.put(label("Hello, Faceless Champ", 960, 360, 68), 769, until=797)
    dot = a.put(Circle(44, fill=ACCENT, stroke=None, position=(600, 550)), 771, until=797)
    a.motion(dot, lambda c: c.animate.move_to(1320, 550), 774, duration=1.8)
    a.text("preview → refine", 960, 748, 779, size=34, color=MUTED, until=797)
    a.flow(ctx, ("Python", "timeline", "MP4"), 797, bounds=Bounds(280, 370, 1640, 600))
    for cue, x in ((807, 510), (812, 960), (814, 1410)):
        a.put(Circle(10, fill=ACCENT, stroke=None, position=(x, 665)), cue)


BUILDERS = {
    "opening": opening,
    "model": model,
    "setup": setup,
    "author": author,
    "coordinates": coordinates,
    "circle": circle,
    "timeline": timeline,
    "export": export,
    "edits": edits,
    "narration": narration,
    "kit": kit,
    "recap": recap,
}


def build_video():
    ctx = context()
    audio = require_audio()
    assets = {name: ctx.playground(script) for name, script in lesson_scripts().items()}
    cues = track()
    video = Video(ctx)
    video.narration(audio=audio, subtitles=PROJECT / "cue-per-word.srt", captions=False, overlap_tolerance=0.001)
    events = []
    for chapter in chapters():
        with video.segment(
            chapter["id"], start=chapter["start"], duration=chapter["end"] - chapter["start"]
        ) as segment:
            BUILDERS[chapter["id"]](Artist(segment, cues, events), ctx, assets)
    compiled = video.compile()
    report = compiled.report
    report.update(
        chapters=chapters(),
        events=events,
        prepared_assets=ctx.prepared_assets,
        duration=compiled.duration,
        full_export_verified=False,
        source_audio=str(PROJECT / "audio.mp3"),
        audio_tail_policy="preserve source; pad silence only",
    )
    return compiled.composition, report
