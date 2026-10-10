"""Cue-selected content, layouts and motions for the Programming Value film."""

from facelesschamp_kit import BlockBuild, Video
from facelesschamp_kit.blocks import FlowDiagram, Heading, ImageCard, TextPanel

from faceless_champ import (
    Bounds,
    Circle,
    Draw,
    Group,
    Number,
    Polyline,
    PopIn,
    Rectangle,
    Text,
    Typewriter,
    fit_text,
)

from .design import ACCENT, BODY, CANVAS, CHAPTERS, INK, LEFT, MUTED, NOTE, RIGHT, SURFACE, THEME, TITLE


def window(segment, first, following=None):
    # Project authoring shorthand: all timing is translated by the public kit API.
    start = 0 if first == 1 else segment.cue_time(first)
    end = segment.duration if following is None else segment.cue_time(following)
    return start, end - start


def shot(segment, first, following, title, note=""):
    at, duration = window(segment, first, following)
    handle = segment.add(Heading(title), bounds=TITLE, at=at, duration=duration, enter="fade")
    if following is not None:
        segment.play(handle, lambda c: c.animate.opacity_to(0), at=at + duration - 0.22, duration=0.22)
    if note:
        segment.add_core(
            lambda ctx, box: fit_text(note, box, font_size=40, min_font_size=28, color=ACCENT),
            bounds=NOTE,
            at=at,
            duration=duration,
            enter="fade",
        )
    return at, duration


def panels(segment, following, items, columns=2, bounds=BODY):
    # These card positions and words are specific to this story, not an engine.
    rows = (len(items) + columns - 1) // columns
    gap = 28
    w = (bounds.width - gap * (columns - 1)) / columns
    h = (bounds.height - gap * (rows - 1)) / rows
    handles = []
    for i, (cue, title, text) in enumerate(items):
        at, life = window(segment, cue, following)
        x, y = bounds.left + (i % columns) * (w + gap), bounds.top + (i // columns) * (h + gap)
        handle = segment.add(
            TextPanel(text, title=title),
            bounds=Bounds(x, y, x + w, y + h),
            at=at,
            duration=life,
            enter=None,
        )
        segment.play(handle, lambda c: PopIn(c, from_scale=0.92, overshoot=1.02), at=at, duration=0.35)
        handles.append(handle)
    return handles


def code_editor(ctx, box, *, ai):
    bg = Rectangle(
        width=box.width - 8, height=box.height - 8, corner_radius=24, fill=SURFACE, stroke=None, position=box.center
    )
    label = fit_text(
        "AI / GENERATED" if ai else "HUMAN / MANUAL",
        Bounds(box.left + 40, box.top + 30, box.right - 40, box.top + 92),
        font_size=32,
        color=ACCENT if ai else INK,
    )
    code = Text(
        "def build_idea():\n    understand(problem)\n    connect(the_parts)\n    return useful_system",
        position=(box.center[0], box.center[1] + 35),
        font_size=38,
        spacing=12,
        color=INK,
    )
    dots = [
        Circle(radius=7, fill=ACCENT if ai else MUTED, stroke=None, position=(box.left + 40 + i * 24, box.top + 115))
        for i in range(3)
    ]
    return BlockBuild(Group(bg, label, code, *dots), {"code": code})


def opening(s, image_mode):
    shot(s, 1, 21, "AI can write the code.", "Faster output. A bigger question.")
    at, life = window(s, 1, 21)
    human = s.add_core(lambda ctx, box: code_editor(ctx, box, ai=False), bounds=LEFT, at=at, duration=life)
    ai = s.add_core(lambda ctx, box: code_editor(ctx, box, ai=True), bounds=RIGHT, at=at, duration=life)
    s.play(human["code"], Typewriter, at=s.cue_time(4), duration=5.8)
    s.play(ai["code"], Typewriter, at=s.cue_time(4), duration=1.6)
    shot(s, 21, 54, "Why learn to code?", "When the machine can already write it")
    at, life = window(s, 21, 54)
    s.add(ImageCard("art-1", mode=image_mode), bounds=RIGHT, at=at, duration=life, enter="fade")
    panels(s, 54, [(21, "THE QUESTION", "What is programming actually worth?")], columns=1, bounds=LEFT)

    shot(s, 54, 68, "The prediction", "A familiar story about the future")
    claims = panels(
        s,
        68,
        [(54, "PROGRAMMING", "Dead?"), (57, "DEVELOPERS", "Replaced?"), (61, "LEARNING", "Pointless?")],
        columns=3,
    )
    for h, cue in zip(claims, (56, 60, 67)):
        s.play(h, lambda c: c.animate.scale_to(0.94), at=s.cue_time(cue), duration=0.25)
    shot(s, 68, 106, "What if the value is shifting?", "Code gets easier. Understanding matters more.")
    at, life = window(s, 68, 106)
    h = s.add(
        FlowDiagram(("More powerful AI", "Easier production", "Better judgment")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )
    s.play(h["node-2"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(85), duration=0.45)
    shot(s, 106, 173, "The old model: writing instructions", "Languages → syntax → working software")
    panels(
        s,
        173,
        [
            (117, "Language", "Tell the machine"),
            (131, "Syntax", "Write the rules"),
            (135, "Structure", "Loops · functions · classes"),
            (147, "Output", "Working software"),
        ],
    )
    shot(s, 173, 210, "Production gets easier", "Hours of mechanics can become a few prompts")
    at, life = window(s, 173, 210)
    h = s.add(
        FlowDiagram(("Documentation", "Debugging", "Boilerplate", "A few prompts")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="fade",
    )
    for i, cue in enumerate((189, 191, 193)):
        s.play(h[f"node-{i}"], lambda c: c.animate.scale_to(0.88), at=s.cue_time(cue), duration=0.45)
    s.play(h["node-3"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(201), duration=0.45)
    shot(s, 210, 232, "The economics change", "Conceptual relationship · not measured market data")
    panels(
        s,
        232,
        [(210, "Production cost ↓", "Writing the code"), (218, "Decision value ↑", "Knowing what it should do")],
        bounds=Bounds(96, 750, 1824, 1000),
    )
    at, life = window(s, 210, 232)

    def curves(ctx, box):
        down = Polyline(
            ((300, 505), (480, 540), (670, 635), (835, 690)), stroke=ACCENT, stroke_width=7, line_cap="round"
        )
        up = Polyline(
            ((1095, 690), (1260, 635), (1445, 540), (1620, 505)), stroke=INK, stroke_width=7, line_cap="round"
        )
        return BlockBuild(Group(down, up), {"down": down, "up": up})

    # Curves occupy a reserved upper strip; cards sit below them.
    # Use a fresh composition rather than a raster chart with invented numbers.
    curves_handle = s.add_core(curves, bounds=Bounds(260, 460, 1660, 730), at=at, duration=life, z_index=2)
    s.play(curves_handle["down"], Draw, at=s.cue_time(212), duration=1.6)
    s.play(curves_handle["up"], Draw, at=s.cue_time(218), duration=2)
    shot(
        s, 232, 258, "An app that works… or an app that helps?", "Same ability to generate code. Different usefulness."
    )
    panels(s, 258, [(232, "WORKS", "Features without a real need"), (242, "USEFUL", "A problem worth solving")])
    shot(s, 258, 300, "Choose the right problem", "Connect the parts. Anticipate failure. Design a solution.")
    panels(
        s,
        300,
        [
            (262, "Recognize", "The right problem"),
            (267, "Connect", "How the pieces interact"),
            (273, "Anticipate", "What could go wrong"),
            (280, "Design", "A solution that makes sense"),
        ],
    )
    shot(s, 300, None, "Programming is a way of thinking.")
    at, life = window(s, 300)
    s.add(
        FlowDiagram(("Problem", "Understanding", "Useful system")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )


def systems(s, image_mode):
    shot(s, 306, 339, "See connections, not isolated tasks.", "Inputs · outputs · dependencies · feedback")
    panels(s, 339, [(309, "Tasks", "Separate pieces"), (325, "Systems", "Relationships between pieces")])
    shot(s, 339, 380, "A small business, five kinds of work", "What looks like five jobs has one underlying structure")
    at, life = window(s, 339, 380)
    s.add(ImageCard("art-2", mode=image_mode), bounds=LEFT, at=at, duration=life, enter="fade")
    panels(
        s,
        380,
        [
            (345, "Receive", "Customer requests"),
            (349, "Organize", "Information"),
            (351, "Update", "Spreadsheets"),
            (353, "Generate", "Invoices"),
            (356, "Follow up", "Emails"),
        ],
        columns=2,
        bounds=RIGHT,
    )
    shot(s, 380, 410, "One interconnected system", "Information enters → transforms → produces an outcome")
    at, life = window(s, 380, 410)
    flow = s.add(
        FlowDiagram(("Requests", "Information", "Sheet", "Invoice", "Follow-up")), bounds=BODY, at=at, duration=life
    )
    for i in range(4):
        s.play(flow[f"edge-{i}"], Draw, at=at + i * 0.35, duration=0.45)
    token_start = s.cue_time(383)
    s.add_core(
        lambda ctx, box: Group(
            Polyline(((242, 845), (1678, 845)), stroke=MUTED, stroke_width=2),
            fit_text("INFORMATION", Bounds(650, 886, 1250, 946), font_size=32, color=INK),
        ),
        bounds=Bounds(200, 810, 1750, 980),
        at=token_start,
        duration=at + life - token_start,
        enter="fade",
        enter_duration=0.25,
    )
    token = s.add_core(
        lambda ctx, box: Circle(radius=13, fill=ACCENT, stroke=None, position=(242, 845)),
        bounds=Bounds(200, 810, 1750, 880),
        at=token_start,
        duration=at + life - token_start,
        enter="pop",
        enter_duration=0.25,
    )
    s.play(token, lambda c: c.animate.move_to(960, 845), at=s.cue_time(388), duration=1.8)
    s.play(token, lambda c: c.animate.move_to(1678, 845), at=s.cue_time(394), duration=1.5)
    shot(s, 410, 440, "Now ask better workflow questions", "The structure makes improvement possible")
    panels(
        s,
        440,
        [
            (410, "Repeat?", "Why do this manually?"),
            (417, "Automate?", "Can the system do it?"),
            (421, "Duplicate?", "Why enter it twice?"),
            (430, "Redesign?", "Improve the whole workflow"),
        ],
    )
    shot(s, 440, None, "Recognize the structure. Improve it.", "From repeated steps to one connected workflow")
    at, life = window(s, 440)
    flow = s.add(
        FlowDiagram(("Enter once", "Transform", "Deliver")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )
    s.play(flow["node-1"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(469), duration=0.45)


def optimization(s):
    shot(s, 477, 506, "Making it work is only the beginning.", "A correct answer is the first milestone")
    at, life = window(s, 477, 506)
    s.add(
        FlowDiagram(("Input", "Correct answer", "What happens at scale?")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )
    shot(s, 506, 539, "What happens when the system grows?", "Hypothetical examples from the narration")
    values = (
        (506, 516, 1, 1000, "DATA", "×", ""),
        (518, 524, 10, 10000000, "USERS", "", ""),
        (526, 537, 1, 1000, "COST", "$", ""),
    )
    for i, (first, change, old, new, label, prefix, suffix) in enumerate(values):
        at, life = window(s, first, 539)
        x = 96 + i * 585
        box = Bounds(x, 430, x + 555, 910)

        def metric(ctx, box, old=old, label=label, prefix=prefix, suffix=suffix):
            background = Rectangle(
                width=box.width - 8,
                height=box.height - 8,
                fill=SURFACE,
                stroke=None,
                corner_radius=24,
                position=box.center,
            )
            value = Number(
                old,
                prefix=prefix,
                suffix=suffix,
                font_size=78,
                color=ACCENT,
                width=box.width - 44,
                position=(box.center[0], box.center[1] - 20),
            )
            title = fit_text(
                label, Bounds(box.left + 20, box.bottom - 120, box.right - 20, box.bottom - 40), font_size=36, color=INK
            )
            return BlockBuild(Group(background, value, title), {"value": value})

        h = s.add_core(metric, bounds=box, at=at, duration=life)
        s.play(h, lambda c: PopIn(c, from_scale=0.92, overshoot=1.02), at=at, duration=0.4)
        s.play(h["value"], lambda c, new=new: c.animate.value_to(new), at=s.cue_time(change), duration=0.7)
    shot(s, 539, 558, "Efficiency is a set of trade-offs.", "Time · memory · resources · scalability")
    panels(
        s,
        558,
        [
            (546, "Efficiency", "Less wasted work"),
            (547, "Time", "How fast?"),
            (549, "Memory", "How much space?"),
            (551, "Resources", "At what cost?"),
            (552, "Trade-offs", "Choose deliberately"),
            (557, "Scale", "Keep it useful"),
        ],
        columns=3,
    )
    shot(s, 558, 591, "The same thinking improves daily work.", "Notice repetition and unnecessary steps")
    at, life = window(s, 558, 591)
    s.add(
        FlowDiagram(("Do work", "Notice repetition", "Find a better pattern")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )
    shot(s, 591, None, "Four ways to improve a process", "Programming changes how you approach problems")
    panels(
        s,
        None,
        [
            (599, "Simplify", "Fewer steps"),
            (600, "Delegate", "The right owner"),
            (601, "Automate", "Repeat reliably"),
            (603, "Eliminate", "Remove needless work"),
        ],
    )


def better_questions(s, image_mode):
    shot(s, 620, 664, "Same AI. Different approach.", "Both people have access to the same model")
    panels(
        s,
        664,
        [
            (629, "Person one", "Build me a productivity app"),
            (648, "The result", "Code + interface + a working application"),
        ],
    )
    shot(s, 664, 718, "The second person asks…", "Seven questions before adding more features")
    # Six cards plus a full-width seventh: a deliberate change of composition.
    panels(
        s,
        718,
        [
            (674, "Audience", "Who is it for?"),
            (680, "Problem", "What does it solve?"),
            (685, "Data", "What must be stored?"),
            (691, "Mistakes", "What can go wrong?"),
            (699, "Cost", "What is expensive?"),
            (703, "Growth", "What happens at scale?"),
        ],
        columns=3,
        bounds=Bounds(96, 400, 1824, 800),
    )
    panels(
        s, 718, [(709, "Restraint", "Which features should not exist?")], columns=1, bounds=Bounds(96, 832, 1824, 1000)
    )
    shot(s, 718, 771, "Understanding changes the outcome.", "Better questions → better trade-offs → better evaluation")
    at, life = window(s, 718, 771)
    flow = s.add(
        FlowDiagram(("Ask", "Compare", "Evaluate")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )
    for i, cue in enumerate((748, 751, 755)):
        s.play(flow[f"node-{i}"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(cue), duration=0.4)
    shot(s, 771, 814, "From production skill to thinking skill", "Technical knowledge still matters")
    panels(
        s,
        814,
        [
            (780, "Production", "Writing instructions"),
            (790, "Thinking", "Understanding systems"),
            (809, "Reliability", "Secure and correct"),
            (812, "Complexity", "Know how the parts interact"),
        ],
    )
    shot(s, 814, 870, "Useful beyond professional software", "Ideas become testable systems")
    at, life = window(s, 814, 870)
    s.add(ImageCard("art-3", mode=image_mode), bounds=LEFT, at=at, duration=life, enter="fade")
    panels(
        s,
        870,
        [
            (828, "Researcher", "Automate experiments"),
            (836, "Designer", "Prototype ideas"),
            (847, "Creator", "Remove repetitive work"),
            (857, "Entrepreneur", "Test before investing"),
        ],
        bounds=RIGHT,
    )
    shot(s, 870, None, "Turn an idea into a working system.", "AI makes that ability accessible to more people")
    at, life = window(s, 870)
    s.add(
        FlowDiagram(("Idea", "Prototype", "Useful system")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )


def human_judgment(s, image_mode):
    shot(s, 903, 924, "One missing piece: human understanding.")
    at, life = window(s, 903, 924)
    s.add(
        FlowDiagram(("AI capability", "Human context", "Useful outcome")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )
    shot(s, 924, 969, "AI's capabilities are extraordinary.", "Take the tools seriously")
    panels(
        s,
        969,
        [
            (926, "Generate", "Code"),
            (928, "Analyze", "Complex systems"),
            (931, "Propose", "Architectures"),
            (933, "Discover", "Patterns"),
            (937, "Create", "New ideas"),
            (965, "Improve", "Growing capability"),
        ],
        columns=3,
    )
    shot(s, 969, 987, "Solving a problem ≠ choosing the problem", "Which problem deserves to be solved?")
    panels(s, 987, [(975, "Solve", "A specified problem"), (980, "Choose", "A problem worth solving")])
    shot(
        s,
        987,
        1042,
        "Context comes from a life being lived.",
        "Needs · relationships · responsibilities · consequences",
    )
    at, life = window(s, 987, 1042)
    s.add(ImageCard("art-4", mode=image_mode), bounds=LEFT, at=at, duration=life, enter="fade")
    panels(
        s,
        1042,
        [
            (1003, "Frustrations", "Your daily experience"),
            (1010, "Relationships", "People you care about"),
            (1015, "Responsibilities", "What you carry"),
            (1027, "Consequences", "What decisions mean for you"),
        ],
        bounds=RIGHT,
    )
    shot(s, 1042, 1077, "An impressive solution can still be wrong.", "Human judgment chooses what matters")
    panels(
        s,
        1077,
        [
            (1049, "Worth building", "A meaningful outcome"),
            (1056, "Acceptable trade-offs", "Your priorities"),
            (1063, "Technically impressive", "Does it solve the right problem?"),
            (1073, "Human judgment", "Evaluate the real consequences"),
        ],
    )
    shot(s, 1077, None, "Translate human intentions into systems.")
    at, life = window(s, 1077)
    s.add(
        FlowDiagram(("Human intention", "Programming", "A system that acts")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )


def useful_systems(s):
    shot(s, 1102, 1160, "The reason to learn is changing.", "Tasks get cheaper. Jobs and advantages change.")
    panels(
        s,
        1160,
        [
            (1112, "Production", "Some tasks cost less"),
            (1119, "Jobs", "Roles change"),
            (1125, "Syntax", "Less advantage on its own"),
            (1142, "Understanding", "Still worth learning"),
        ],
    )
    shot(s, 1160, 1198, "Understand what needs to be built.", "Why it matters. How the pieces fit.")
    panels(s, 1198, [(1160, "Most code", "Quantity of output"), (1174, "Useful systems", "Quality of understanding")])
    shot(
        s,
        1198,
        1247,
        "Break complexity into understandable parts.",
        "Recognize inefficiency. Guide AI. Evaluate usefulness.",
    )
    at, life = window(s, 1198, 1247)
    flow = s.add(
        FlowDiagram(("Complex problem", "Smaller parts", "Useful solution")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )
    s.play(flow["node-0"], lambda c: c.animate.scale_to(0.85), at=s.cue_time(1207), duration=0.6)
    s.play(flow["node-2"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(1245), duration=0.4)
    shot(s, 1247, 1293, "Learn to think like a programmer.", "More than memorizing syntax")
    panels(
        s,
        1293,
        [
            (1276, "Systems", "Understand connections"),
            (1281, "Patterns", "Recognize structure"),
            (1286, "Design", "Question the choices"),
            (1291, "Optimize", "Improve the process"),
        ],
    )
    shot(s, 1293, 1329, "Someone must understand the goal.", "More understanding opens more possibilities")
    at, life = window(s, 1293, 1329)
    s.add(
        FlowDiagram(("AI writes code", "You understand why", "New possibilities")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=0.9,
    )
    shot(s, 1329, None, "Make complexity understandable.", "Turn ideas into something real.")
    at, life = window(s, 1329)
    flow = s.add(
        FlowDiagram(("Complexity", "Understanding", "Something real")),
        bounds=BODY,
        at=at,
        duration=life,
        enter="stagger",
        enter_duration=1,
    )
    s.play(flow["node-0"], lambda c: c.animate.scale_to(0.86), at=s.cue_time(1344), duration=0.6)
    s.play(flow["node-2"], lambda c: c.animate.scale_to(1.04), at=s.cue_time(1349), duration=0.7)
    s.play(flow["label-1"], lambda c: c.animate.color_to(ACCENT), at=s.cue_time(1370), duration=0.6)


def build(ctx, image_mode="auto"):
    ctx.canvas, ctx.theme = CANVAS, THEME
    video = Video(ctx)
    voice = video.narration(
        audio="audio.mp3",
        subtitles="cue-per-word.srt",
        markers={name: first for name, first, _ in CHAPTERS},
        captions=False,
        overlap_tolerance=0.001,
    )
    authors = (opening, systems, optimization, better_questions, human_judgment, useful_systems)
    for (name, first, following), author in zip(CHAPTERS, authors):
        start = 0 if first == 1 else voice.track.cue(first).start
        end = voice.track.cue(following).start if following else voice.duration
        segment = video.segment(name, start=start, duration=end - start)
        if name in {"code-value", "systems", "better-questions", "human-judgment"}:
            author(segment, image_mode)
        else:
            author(segment)
    return video
