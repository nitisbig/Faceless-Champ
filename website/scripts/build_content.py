"""Generate the guide and downloadable examples from one content source."""
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
EXAMPLES = DIST / 'examples'
EXAMPLES.mkdir(parents=True, exist_ok=True)
lessons = []

def code(source, language='python', filename=None, target=None, kind='core', template='silent'):
    source = textwrap.dedent(source).strip() + '\n'
    result = dict(type='code', language=language, code=source)
    if filename:
        (EXAMPLES / filename).write_text(source)
        result.update(filename=filename, target=target, kind=kind)
        result['command'] = (f'faceless-champ render {filename} {target} -o output/{Path(filename).stem}.mp4 -q ql'
                             if kind == 'core' else 'fc-kit preview main -o output/preview.mp4')
        if kind == 'kit':
            result['template'] = template
            result['placement'] = f'Save as videos/main.py in a project created with --template {template}.'
    return result

def section(title, text, *blocks):
    return dict(title=title, text=text, blocks=list(blocks))

def note(text):
    return dict(type='note', text=text)

def link(text, href):
    return dict(type='link', text=text, href=href)

def lesson(id, title, group, description, sections, preview=None, *, guide='core', portrait=False):
    lessons.append(dict(id=id, title=title, group=group, description=description, sections=sections,
                        preview=preview, guide=guide, portrait=portrait))

hello = code('''
from faceless_champ import Scene, Text, Circle, Typewriter, FadeIn

class Hello(Scene):
    def construct(self):
        title = Text("Hello, world!", font_size=100,
                     position=(960, 400), color="#edf2fc")
        dot = Circle(60, fill="#48e0cb", stroke=None,
                     position=(400, 700))
        self.play(Typewriter(title), FadeIn(dot), run_time=1.5)
        self.play(dot.animate.move_to(1520, 700), run_time=1)
        self.wait(0.5)
''', filename='hello.py', target='Hello')
lesson('hello-world', 'Hello, world!', 'Start here', 'A few lines of Python. Your first animated video. Start with a scene, add something worth seeing, and bring it to life.', [
section('Write your first scene', 'Save this as hello.py. A Scene is your timeline; construct() describes what happens on it.', hello),
section('Render it', 'Run this in the directory containing hello.py after completing Installation. The ql preset exports a 720p preview from the default 1920 × 1080 design canvas.', code('faceless-champ render hello.py Hello -o output/hello.mp4 -q ql', 'bash')),
section('Read the timeline', 'The text and circle enter together over 1.5 seconds. The next play() moves the circle for one second. wait(0.5) holds the final frame. Total duration: three seconds.', note('Multiple animations in one play() run together. Separate play() calls run one after another.')),
section('Try a change', 'Change the message, the circle color, or run_time. Use --overwrite to replace an existing export.', code('faceless-champ render hello.py Hello -o output/hello.mp4 -q ql --overwrite', 'bash')),
], 'hello')
lesson('installation', 'Installation', 'Start here', 'Set up the core Python video engine, its command line, and FFmpeg.', [
section('Get the repository', 'Install the current core library from source in a Python 3.12+ environment.', code('''
git clone https://github.com/nitisbig/Faceless-Champ.git
cd Faceless-Champ
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
''', 'bash')),
section('Install FFmpeg', 'On Ubuntu, install FFmpeg for MP4 encoding and ffprobe for inspecting exports. The FFmpeg build must include the libx264 encoder.', code('''
sudo apt install ffmpeg
ffmpeg -version
ffprobe -version
faceless-champ --help
''', 'bash')),
section('Optional capabilities', 'Charts, shapes, text, and motion graphics use the core Pillow dependency. Equations need Matplotlib; maps need NumPy. Install only the extras you use.', code('python -m pip install -e ".[equations,maps]"', 'bash')),
section('Two packages, two jobs', 'This guide covers faceless_champ: components, animation, timelines, and rendering. For structured projects, reusable blocks, and templates, use the framework guide.', link('Open the facelesschamp-kit guide →', 'kit.html'))
])
canvas = code('''
from faceless_champ import Canvas, Circle, Scene, Text, FadeIn

scene = Scene(Canvas(1080, 1920, "#0b101b"))
scene.add(Text("Made with Python", font_size=72,
               position=(540, 760), color="#edf2fc"))
scene.play(FadeIn(Circle(90, fill="#48e0cb", stroke=None,
                         position=(540, 1100))), run_time=1)
scene.wait(1)
''', filename='portrait.py', target='scene')
lesson('scenes-and-canvas', 'Scenes & canvas', 'Library fundamentals', 'Think in design pixels. Render the same composition at a smaller resolution without rewriting its layout.', [
section('Choose a canvas', 'Canvas(width, height, bg) defines the design space. The default is 1920 × 1080. For a vertical Short, use 1080 × 1920.', canvas),
section('Export a portrait preview', 'Coordinates, text sizes, and strokes scale with the output. Supply both dimensions and keep the design aspect ratio.', code('faceless-champ render portrait.py scene -o output/portrait.mp4 --width 540 --height 960 --fps 15 --antialias 1', 'bash')),
section('Understand coordinates', 'The top-left is (0, 0); x moves right and y moves down. Components are centered on their position by default. Use anchor="top_left" for a top-left placement. Positive rotation turns clockwise.', note('A component added with add() appears immediately at the current cursor. An entrance passed to play() can add its target automatically.'))
])
text_shapes = code('''
from faceless_champ import Canvas, Scene, Text, Rectangle, Group, PopIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=900, height=360, corner_radius=28,
                 fill="#172238", stroke="#48e0cb", stroke_width=3,
                 position=(960, 540))
title = Text("Build with Python", font_size=72,
             color="#edf2fc", position=(960, 490))
label = Text("Text. Shapes. A timeline.", font_size=32,
             color="#8996ad", position=(960, 590))
scene.play(PopIn(Group(card, title, label)), run_time=0.6)
scene.wait(1.4)
''', filename='text_shapes.py', target='scene')
lesson('text-and-shapes', 'Text & shapes', 'Library fundamentals', 'Build a visual vocabulary from readable typography and simple geometry.', [
section('Compose a title card', 'Use Text, Circle, Rectangle, Arrow, and Polyline as ordinary components. Combine a background and labels into one Group for a shared entrance.', text_shapes),
section('Typography that fits', 'font_size is measured in design pixels. The core Text component uses explicit newlines; it does not wrap automatically. Pass a local font file with font= for custom typography. The kit adds measured wrapping and shrinking inside blocks.', code('''
from faceless_champ import Text

label = Text("One idea.\\nTwo lines.", font_size=64,
             color="#48e0cb", position=(960, 540))
''')),
section('Style before scheduling', 'Set fill, stroke, opacity, scale, and rotation before adding a component. Once it is on the timeline, use its animation builder for a timed change.', note('Finish Group membership and initial layout before adding the group to a scene.'))
], 'text-shapes')
timing = code('''
from faceless_champ import Canvas, Scene, Text, FadeIn, FadeOut

scene = Scene(Canvas(1920, 1080, "#0b101b"))
first = Text("First, the question.", font_size=72, position=(960, 460))
second = Text("Then, the evidence.", font_size=56, position=(960, 600))
scene.play(FadeIn(first), run_time=0.5)
with scene.at(1.5):
    scene.play(FadeIn(second), run_time=0.5)
scene.wait_until(3)
scene.play(FadeOut(first), FadeOut(second), run_time=0.5)
scene.wait(0.5)
''', filename='timing.py', target='scene')
lesson('timeline-and-timing', 'Timeline & timing', 'Library fundamentals', 'Author sequential beats or schedule independent visuals at exact times.', [
section('Schedule an absolute beat', 'play() advances the cursor; wait() adds a hold. at(seconds) schedules an independent block at an absolute time, then restores the furthest cursor. wait_until() holds to a specific time.', timing),
section('Avoid conflicting tracks', 'Animate the same property in chronological order. Writes to the same property cannot overlap. Different properties and different components can animate together.', note('Add a final hold so viewers can read the completed state. Audio does not advance the visual cursor, but its tail can extend a scene.'))
])
groups = code('''
from faceless_champ import Canvas, Circle, Group, Text, Scene, FadeIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
cards = []
for word in ("Compose", "Animate", "Export"):
    dot = Circle(50, fill="#48e0cb", stroke=None)
    label = Text(word, font_size=36).next_to(dot, direction="down", gap=24)
    cards.append(Group(dot, label))
diagram = Group(*cards).arrange(direction="right", gap=120).move_to(960, 540)
scene.play(FadeIn(diagram), run_time=0.7)
scene.play(diagram.animate.scale_to(1.15), run_time=0.8)
scene.wait(0.5)
''', filename='groups.py', target='scene')
lesson('groups-and-layout', 'Groups & layout', 'Library fundamentals', 'Keep related visuals together and let measured bounds guide placement.', [
section('Arrange a small diagram', 'next_to() uses the measured edge of another component. Group.arrange() adds consistent spacing, and move_to() places the whole result.', groups),
section('Measure before you move', 'Use component.bounds for initial geometry and align_to(other, edge="left") for alignment. For an animated object, scene.bounds_at(component, time) measures its evaluated world-space box.', note('Group transforms apply after member coordinates. Independent member animations use the original member coordinate system.'))
])
media = code('''
from pathlib import Path
from faceless_champ import Canvas, Scene, ImageSlot, FadeIn

ASSETS = Path(__file__).resolve().parent / "assets"
scene = Scene(Canvas(1920, 1080, "#0b101b"))
image = ImageSlot(ASSETS / "photo.png", width=1000, height=620,
                  position=(960, 540), fit="cover", mode="auto")
scene.play(FadeIn(image), run_time=0.5)
scene.wait(1.5)
''', filename='images.py', target='scene')
lesson('images-and-audio', 'Images & audio', 'Library fundamentals', 'Bring local media into the composition and keep asset paths predictable.', [
section('Reserve an image slot', 'ImageSlot in auto mode displays a labeled placeholder until the file exists. mode="required" fails when it is missing; mode="placeholder" always reserves the space. Corrupt present files are errors.', media),
section('Normalize an image', 'Image.from_source() accepts a local path, encoded bytes, or a Pillow image. trim=True removes transparent margins; tint= applies a monochrome color.', code('''
from faceless_champ import Image

# Requires your own local file.
logo = Image.from_source("assets/logo.png", width=200, height=200,
                         trim=True, position=(960, 540))
''')),
section('Place audio explicitly', 'This snippet requires your own music.wav. Use start=0 for scene-start audio; the default start is the current cursor. Audio can extend beyond the last visual command.', code('''
scene.add_audio(ASSETS / "music.wav", start=0, trim_end=2,
                volume=0.3, fade_in=0.2, fade_out=0.4)
'''), note('Images and audio resolve from your scene file in these examples. Create a fresh renderer after replacing an asset.'))
])
charts = code('''
from faceless_champ import Axis, BarChart, Canvas, ChartReveal, Scene, Text

scene = Scene(Canvas(1920, 1080, "#0b101b"))
chart = BarChart(
    ["Q1", "Q2", "Q3"], {"Completed": [3, 5, 4]},
    width=1200, height=650, position=(960, 520),
    title="Project milestones", y_axis=Axis(limits=(0, 10)),
)
scene.add(Text("SYNTHETIC EXAMPLE DATA", font_size=24,
               color="#8996ad", position=(960, 960)))
scene.play(ChartReveal(chart), run_time=1)
scene.play(chart.animate.data_to({"Completed": [5, 7, 9]}), run_time=1.5)
scene.wait(0.5)
''', filename='charts.py', target='scene')
lesson('charts-and-numbers', 'Charts & numbers', 'Library fundamentals', 'Reveal data, animate values, and keep axes meaningful throughout a transition.', [
section('Animate a dataset', 'Charts are core components. Supply ordinary Python data, reveal it with ChartReveal, and update matching data shapes with data_to(). This example uses synthetic data, labeled on screen.', charts),
section('Keep the domain stable', 'Most charts derive automatic limits once from the initial data. Supply Axis(limits=...) to cover every keyframe. Keep category order, series shape, and graph topology fixed when transitioning.', dict(type='table',headers=['Component','Input'],rows=[['BarChart','Categories + named value series'],['LineChart / ScatterPlot','Named sequences of (x, y) pairs'],['RankedBarChart','Name → value or None'],['Number','Value + format_spec / formatter'],['Heatmap / Histogram','Matrix / sample values'],['NetworkGraph / SankeyChart','Nodes and edges / weighted links']])),
section('Animate a counter', 'Add the number before animating it. A fixed width keeps its alignment stable as the number of digits changes.', code('''
from faceless_champ import Number

count = Number(0, format_spec=".0f", width=300,
               font_size=96, position=(960, 540))
scene.add(count)
scene.play(count.animate.value_to(100), run_time=2)
'''), note('Missing observations are not zero. RankedBarChart accepts None and labels missing data explicitly.'))
], 'charts')
lesson('narration-and-cues', 'Narration & cues', 'Library fundamentals', 'Match visuals to the original audio clock using SRT cue timestamps.', [
section('Use original cue numbers', 'The following is an asset-dependent recipe. Supply audio.mp3 and cue-per-word.srt. Pick cue numbers that exist in your track and choose the scene duration to cover the narration.', code('''
from faceless_champ import Scene, Text, FadeIn, Captions, SubtitleTrack

track = SubtitleTrack.from_srt("cue-per-word.srt")
scene = Scene()
scene.add_audio("audio.mp3", start=0)
scene.add(Captions(track, position=(960, 1008)))
with scene.at(track.cue(4).start):
    scene.play(FadeIn(Text("The key idea", font_size=80,
                            position=(960, 540))), run_time=0.3)
scene.wait_until(max(track.duration, scene.duration))
'''),note('Choose an entrance duration that fits the remaining cue window. Keep original SRT indices and timestamps; do not retime the word track.')),
section('Author chapters on a local clock', 'CueScene(track, start_time=..., end_time=...) translates source cues to a chapter clock. at_cue(index) schedules a visual; finish() holds to the exact boundary and rejects overflow. Place continuous narration at zero on a parent Layer and combine chapters with Sequence(crossfade=0).'),
section('Preview without retiming', 'Range exports sample the original source clock and trim the corresponding audio. A cue shorter than one frame may not appear at low frame rates.', code('scene.render("output/cue-preview.mp4", start_time=12, end_time=18,\n             width=960, height=540, fps=15, antialias=1)'))
])
composition = code('''
from faceless_champ import Canvas, Scene, Text, FadeIn, Sequence, Grid

canvas = Canvas(1920, 1080, "#0b101b")
def panel(word):
    scene = Scene(canvas)
    scene.play(FadeIn(Text(word, font_size=120,
                            position=(960, 540))), run_time=0.5)
    scene.wait(1.5)
    return scene

video = Sequence(
    panel("One idea"),
    Grid(panel("A"), panel("B"), rows=1, columns=2,
         gap=24, canvas=canvas),
    panel("One video"),
    crossfade=0.3,
)
''',filename='composition.py',target='video')
lesson('composition', 'Sequence, grid & layer', 'Library fundamentals', 'Combine scenes into a complete video without duplicating authoring logic.', [
section('Build a sequence', 'Sequence plays children one after another. Grid places scenes in cells and plays them together. This example shows an opening, a side-by-side comparison, and a finish.', composition),
section('Account for overlap', 'A crossfade shortens the sequence by its overlap. For narration chapters that must preserve source timestamps, use crossfade=0. Layer overlays scenes on a shared timeline; use a transparent canvas for audio or caption overlays.'),
section('Render the composition', 'The CLI accepts a Scene class, a composition variable, or a zero-argument factory returning a renderable.',code('faceless-champ render composition.py video -o output/composition.mp4 -q ql', 'bash'))
])
kit = code('''
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import MetricCard, Comparison, StepList

def build(ctx):
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        card = segment.add(MetricCard(42, "Reusable components"), enter="pop")
        segment.play(card["value"], lambda number: number.animate.value_to(100),
                     at=1, duration=1)
    with video.segment("comparison", duration=4) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"),
                    enter="fade")
    with video.segment("finish", duration=3) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
''',filename='kit_main.py',kind='kit')
lesson('framework-quickstart', 'Framework quickstart', 'The framework', 'Move from individual scenes to a structured project with reusable blocks and a repeatable workflow.', [
section('Scaffold a project', 'The kit sits on top of the engine. Install it in Installation, then create a silent starter. Every command below runs inside my-video.', code('''
fc-kit init my-video --template silent
cd my-video
fc-kit doctor
fc-kit validate main
''','bash')),
section('Build with segments', 'Replace videos/main.py with this build(ctx) factory. Segments append automatically. Their contents disappear at the segment boundary, and named children let you animate a block’s internals.',kit),
section('Inspect, preview, export', 'Start with a frame, then a storyboard and a short clip. The final render uses the project’s final profile.',code('''
fc-kit frame main --time 1.5 -o output/frame.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main --segment hook -o output/hook.mp4
fc-kit render main -o output/main.mp4
''','bash'),note('facelesschamp-kit 0.1.0rc1 is a local release candidate. The guide uses the implementation in this repository.'))
], 'kit', guide='kit', portrait=True)
lesson('project-configuration', 'Project configuration', 'The framework', 'Keep format, themes, assets, and export settings in a predictable project layout.', [
section('Know the project layout', 'The scaffold separates authoring code from local assets and workflow outputs.', code('''
my-video/
  facelesschamp.toml
  videos/main.py
  components/
  assets/manifest.json
  assets/images/
  assets/audio/
  data/
  output/
''','text')),
section('Set your format and profiles', 'shorts uses a 1080 × 1920 design canvas; landscape uses 1920 × 1080. Changing format rebuilds measured layouts. Omit export dimensions to keep profiles portable across formats.',code('''
schema_version = 1

[project]
name = "my-video"
seed = 0
safe_margin = 64
caption_space = 220

[videos.main]
factory = "videos.main:build"
format = "shorts"
theme = "midnight"
captions = false

[profiles.preview]
fps = 15
antialias = 1
preset = "veryfast"

[profiles.final]
fps = 30
antialias = 2
preset = "medium"
''','toml')),
section('Register local assets', 'Asset paths resolve from the project root. Use ctx.assets.image("photo") in a factory. The following manifest requires a real local photo; source and license fields should describe your own asset.', code('''
{
  "photo": {
    "type": "image",
    "path": "assets/images/photo.png"
  }
}
''','json'),note('CLI output paths resolve from the invoking directory. Use fc-kit --project /absolute/path for projects elsewhere. Final exports reject placeholders unless explicitly allowed.'))
], guide='kit')
blocks = code('''
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Heading, MetricCard
from facelesschamp_kit.layouts import Stack

def build(ctx):
    video = Video(ctx)
    with video.segment("summary", duration=4) as segment:
        segment.add(Stack(
            Heading("Make the idea visible"),
            MetricCard(3, "Purposeful visual beats"),
            gap=40,
        ), enter="stagger")
    return video
''',filename='kit_blocks.py',kind='kit')
lesson('blocks-and-themes', 'Blocks & themes', 'The framework', 'Reusable content definitions compose fresh core components into measured layouts.', [
section('Compose a block layout', 'Stack allocates vertical cells. Split stacks in portrait and uses columns in landscape. Text wraps, then shrinks to the theme minimum; content that still cannot fit fails with a useful error.',blocks),
section('Choose the right block', 'Built-in blocks expose named children for targeted motion. Pass variant="accent" or variant="muted" to Heading, TextPanel, or MetricCard.',dict(type='table',headers=['Block','Content','Named children'],rows=[['Heading','Text','text'],['TextPanel','Text + optional title','background, text, title'],['MetricCard','Value + label','background, value, label'],['ImageCard','Asset + label','background, image, label'],['Comparison','Left + right text','0, 1'],['StepList','Tuple of steps','0, 1, …'],['WhiteboardDrawing','Path and shape specifications','stroke-0, stroke-1, …']])),
section('Keep styling consistent', 'Set theme="midnight", theme="light", or theme="whiteboard" in facelesschamp.toml. Theme values flow into every built-in block. Explicit colors override variants; variants override theme defaults.')
], guide='kit')
custom = code('''
from dataclasses import dataclass
from faceless_champ import Circle, Group, Text
from facelesschamp_kit import BlockBuild, Video

@dataclass(frozen=True)
class Badge:
    label: str

    def compose(self, ctx, bounds):
        circle = Circle(90, fill=ctx.theme.accent, stroke=None,
                        position=bounds.center)
        label = Text(self.label, font_size=32, color=ctx.theme.background,
                     position=bounds.center)
        return BlockBuild(Group(circle, label),
                          {"circle": circle, "label": label})

def build(ctx):
    video = Video(ctx)
    badge = Badge("REUSE")
    for name in ("first", "second"):
        with video.segment(name, duration=3) as segment:
            handle = segment.add(badge, enter="pop")
            segment.play(handle["circle"],
                         lambda circle: circle.animate.scale_to(1.15),
                         at=1, duration=1)
    return video
''',filename='kit_custom.py',kind='kit')
lesson('custom-blocks', 'Your own blocks', 'The framework', 'Turn a repeated visual pattern into a small, reusable Python definition.', [
section('Implement compose()', 'A block defines content, not live component state. compose(context, bounds) creates fresh core components every time the block is placed.',custom),
section('Respect the block contract', 'Return BlockBuild(root, children). Named children must belong to the root hierarchy. Finish grouping and layout before returning; the measured root must fit the supplied bounds. Keep reusable props immutable.',note('Do not store core components on the block definition. Each placement needs independent components and animation tracks.')),
section('Use the engine directly', 'For an advanced visual, segment.add_core(lambda ctx, bounds: component) accepts a factory that returns a fresh Component or BlockBuild. Place the result inside the supplied bounds.')
], guide='kit')
lesson('framework-narration', 'Narrated projects', 'The framework', 'Use narration windows to determine segment lengths and preserve the source clock.', [
section('Start with the narrated template', 'The template includes runnable synthetic demonstration speech and sentence-level SRT cues. It visibly labels the sample. Replace its manifest entries and markers with your own narration.',code('''
fc-kit init narrated-video --template narrated-short
cd narrated-video
fc-kit validate main
fc-kit preview main -o output/preview.mp4
''','bash')),
section('Build cue windows', 'This asset-dependent factory requires voiceover and word_cues entries in assets/manifest.json. Choose existing cue indices for the markers. voice.between() creates exact source-time windows.',code('''
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Heading, Comparison

def build(ctx):
    video = Video(ctx)
    voice = video.narration(
        audio=ctx.assets.audio("voiceover"),
        subtitles=ctx.assets.subtitle("word_cues"),
        markers={"hook": 1, "comparison": 54},
        captions=False,
    )
    with video.segment("hook", window=voice.between("hook", "comparison")) as segment:
        segment.add(Heading("The key question"), enter="fade")
    with video.segment("comparison", window=voice.between("comparison")) as segment:
        segment.add(Comparison("Before", "After"), enter="fade")
    return video
'''),note('Entrance durations must fit each cue window. The final segment holds through an audio tail; the build report identifies that extension.')),
section('Enable captions intentionally', 'Use captions=true in project configuration when you want the kit’s caption overlay. Layout reserves the configured caption space before placing blocks. The bundled template has sentence cues; use your own word-aligned SRT for word highlighting.')
], guide='kit')
properties = code('''
from faceless_champ import Canvas, Rectangle, Scene, Text

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=400, height=220, fill="#48e0cb",
                 stroke="#edf2fc", stroke_width=2, position=(960, 540))
scene.add(card)
scene.play(
    card.animate.fill_to("#708fff").width_to(650).height_to(340)
        .corner_radius_to(48).stroke_width_to(6).rotate_to(8),
    run_time=2,
)
scene.wait(0.5)
''',filename='properties.py',target='scene')
lesson('animated-properties', 'Animated properties', 'Motion graphics', 'Animate position, color, geometry, and transforms through the same timeline.', [
section('Transform several properties together', 'Chain target values on component.animate, then give the animation a duration. The scene resolves its start state from earlier tracks.',properties),
section('Choose the right property', 'Transforms include move_to(), scale_to(), scale_xy_to(), rotate_to(), and opacity_to(). Shape geometry includes width_to(), height_to(), corner_radius_to(), and stroke_width_to(). Text and Number expose color_to().'),
section('Use evaluated bounds', 'component.bounds describes initial authoring geometry. scene.bounds_at(component, time) includes animated dimensions and ancestor transforms. It reserves the full box even when a mask or opacity hides part of the visual.',note('Color interpolation uses straight sRGB channels, including alpha. Use opacity_to() to fade an entire visual. Keep dimensions and scale positive.'))
], 'properties')
schedules = code('''
from faceless_champ import Canvas, Circle, Scene, Stagger, Succession, Repeat, PopIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
dots = [Circle(50, fill="#48e0cb", stroke=None,
               position=(660 + i * 200, 540)) for i in range(4)]
scene.play(Stagger(*(PopIn(dot) for dot in dots), lag=0.2, duration=0.5))
scene.play(Stagger(*(
    Succession(dot.animate.scale_to(1.5), dot.animate.scale_to(1), duration=0.4)
    for dot in dots
), lag=0.15))
scene.play(Repeat(dots[0].animate.opacity_to(0.3),
                  cycles=2, ping_pong=True, duration=0.4))
scene.wait(0.5)
''',filename='schedules.py',target='scene')
lesson('animation-schedules', 'Stagger, sequence & repeat', 'Motion graphics', 'Make complex motion readable by arranging small animations in time.', [
section('Build a finite schedule', 'Stagger offsets children, Succession plays them in order, and Repeat traverses an animation a finite number of times. Nest them to compose a rhythm.',schedules),
section('Understand natural duration', 'duration applies to direct Animation children. Nested schedules retain their own durations. scene.play(schedule) uses the schedule’s natural length; explicit run_time scales the complete schedule.',dict(type='table',headers=['Helper','Behavior'],rows=[['Stagger(..., lag=0.2)','Child i starts at i × lag'],['Succession(...)','Each child follows the previous child'],['Repeat(..., cycles=2, ping_pong=True)','One forward traversal, one reverse traversal']])),
section('Repeat with continuity', 'cycles counts traversals. Two ping-pong cycles return to the initial state. Forward cycles restart their captured values; use a cyclic property or ping-pong when you want continuous motion.',note('Repeat is finite and expands tracks during authoring. Add components at time zero if they should be visible before their first scheduled track.'))
])
masks = code('''
from faceless_champ import Canvas, CircleMask, Group, Rectangle, Scene, Text, Wipe

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=700, height=400, fill="#708fff", stroke=None,
                 position=(960, 540))
stripe = Rectangle(width=760, height=100, fill="#48e0cb", stroke=None,
                   rotation=-20, position=(960, 540))
word = Text("REVEAL", font_size=64, color="#0b101b", position=(960, 540))
visual = Group(card, stripe, word, mask=CircleMask(230))
scene.add(visual)
scene.play(Wipe(visual, direction="right"), run_time=1)
scene.play(visual.animate.mask_to(width=620, height=380), run_time=1)
scene.wait(0.5)
''',filename='masks.py',target='scene')
lesson('masks-and-wipes', 'Masks & wipes', 'Motion graphics', 'Reveal a complete composition through a local clip, or animate the mask itself.', [
section('Clip a group', 'A group mask clips its complete subtree. Attach RectangleMask, CircleMask, or ShapeMask before adding the target to a scene.',masks),
section('Move the reveal', 'Wipe(direction="right"|"left"|"down"|"up") reveals a normalized rectangular clip. It intersects the attached mask. mask_to() animates an existing mask’s local position and dimensions.'),
section('Keep local coordinates clear', 'Masks are centered relative to a sprite center or group pivot. Ancestor transforms apply afterward. Masks affect rendered visibility; they do not reduce the reserved layout bounds.',note('Large canvases and deeply nested masked groups use additional temporary layers. Inspect a small preview before exporting at full resolution.'))
], 'masks')
indicators = code('''
from faceless_champ import (
    Canvas, Scene, ProgressRing, ProgressBar, LoadingDots,
    Countdown, Repeat, linear,
)

scene = Scene(Canvas(1920, 1080, "#0b101b"))
ring = ProgressRing(width=240, height=240, label=True, position=(650, 480))
timer = Countdown(4, font_size=120, position=(1250, 480))
bar = ProgressBar(width=700, height=30, position=(960, 730))
dots = LoadingDots(width=160, height=40, position=(960, 850))
scene.add(ring, timer, bar, dots)
with scene.at(0):
    scene.play(ring.animate.progress_to(1), timer.animate.value_to(0),
               bar.animate.progress_to(1), run_time=4, rate_func=linear)
with scene.at(0):
    scene.play(Repeat(dots.animate.progress_to(1), cycles=4, duration=1),
               rate_func=linear)
scene.wait_until(4.5)
''',filename='indicators.py',target='scene')
lesson('progress-and-indicators', 'Progress & indicators', 'Motion graphics', 'Make waiting, completion, or change visible with explicitly timed motion.', [
section('Tie progress to the timeline', 'Indicators have no independent wall clock. Animate progress_to() from 0 to 1, and animate a Countdown’s value toward zero.',indicators),
section('Choose an indicator', 'ProgressBar fills a track, ProgressRing draws a clockwise ring, Gauge draws a semicircle, LoadingDots loops three dots, and Checkmark draws a completion mark. Countdown is a formatted nonnegative Number.'),
section('Overlap independent motion', 'Both at(0) blocks share the same source clock. The ring and timer take four seconds, while four finite LoadingDots traversals cover the same interval. linear keeps the progress proportional to elapsed time.',note('A progress label needs enough viewport space. Keep progress in [0, 1] and countdown values nonnegative.'))
], 'indicators')
lesson('preview-and-export', 'Preview & export', 'Ship your video', 'Inspect a frame, check a short clip, then render the complete composition.', [
section('Inspect a still and storyboard', 'These helpers save PNGs; they do not export video. Sample times must be inside the composition duration. Run after creating scene from an earlier example.',code('''
from faceless_champ import save_frame, render_storyboard, StoryboardSample

save_frame(scene, 1, "output/frame.png", size=(960, 540))
render_storyboard(scene,
    [StoryboardSample(0.5, "Entrance"), StoryboardSample(1.5, "Result")],
    "output/storyboard", size=(480, 270), columns=2)
''')),
section('Render a source-time excerpt', 'Use the Python render method for a chosen range. The first two seconds here are sampled from the original scene clock.',code('''
scene.render("output/preview.mp4", start_time=0, end_time=2,
             width=960, height=540, fps=15, antialias=1,
             preset="veryfast", overwrite=True)
''')),
section('Export the final scene', 'Use a hold after the last animation, inspect text and layout, then increase resolution and antialiasing for the final export.',code('''
scene.render("output/final.mp4", width=1920, height=1080,
             fps=30, antialias=2, crf=18,
             preset="medium", overwrite=True)
''')),
section('Use the kit workflow', 'Structured kit projects have their own validation and export commands in the framework guide.', link('Kit preview and export →', 'kit.html#kit-preview-and-export'))
])
lesson('troubleshooting', 'Troubleshooting', 'Ship your video', 'Resolve common authoring and export errors with small, specific checks.', [
section('Common fixes', 'Most issues become clear in a small preview or a validation report.',dict(type='table',headers=['Symptom','Fix'],rows=[['FFmpeg / ffprobe missing','Install FFmpeg and check PATH.'],['Unknown encoder libx264','Use a build with the H.264 encoder.'],['Output already exists','Choose another path or use --overwrite.'],['Audio starts late','Use add_audio(..., start=0).'],['Animation overlap','Separate writes to the same property.'],['Invalid dimensions','Supply both even dimensions; preserve aspect ratio.'],['Final state is absent','Add wait() after the last animation.'],['Crossfade is too long','Shorten the fade or lengthen its children.']])),
section('Bound the work', 'Use ql or a 960 × 540 excerpt at 15 fps with antialias=1. Rendering uses a CPU Pillow renderer and streams frames to FFmpeg. Higher resolution, frame rate, antialiasing, and deep masks increase rendering cost.'),
section('Keep the current scope clear', 'The core currently exports MP4. GPU rendering, camera animation, video import, and graphical editing are future work.')
])

lesson('kit-installation', 'Installation', 'Start here', 'Install the framework and its core engine, then check your local video tools.', [
section('Install from this repository', 'Use Python 3.12+ and the kit bundled in this checkout. facelesschamp-kit 0.1.0rc1 is a local release candidate; these instructions do not assume a published release.', code('''
git clone https://github.com/nitisbig/Faceless-Champ.git
cd Faceless-Champ
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e . -e ./facelesschamp-kit
''', 'bash')),
section('Check FFmpeg and the engine', 'Install FFmpeg and ffprobe with the libx264 encoder. doctor checks Python, encoding tools, output access, and optional dependencies.', code('''
sudo apt install ffmpeg
fc-kit doctor
fc-kit list templates
''', 'bash')),
section('Add optional capabilities', 'The core handles rendering; the kit handles projects, blocks, assets, and templates. Geometry-only whiteboards need no extra dependencies. For equations or maps, install the matching extras from the repository root.', code('python -m pip install -e ".[equations,maps]" -e "./facelesschamp-kit[equations,maps]"', 'bash'), link('Learn the core components and animations →', 'index.html')),
], guide='kit')

silent_template = code('''
from facelesschamp_kit.templates import silent


def build(ctx):
    return silent(ctx, value=3, label="Steps from idea to video")
''', filename='kit_silent.py', kind='kit')
narrated_template = code('''
from facelesschamp_kit.templates import narrated


def build(ctx):
    return narrated(
        ctx,
        audio="voiceover",
        subtitles="word_cues",
        markers={"hook": 1, "comparison": 2, "finish": 3},
    )
''', filename='kit_narrated.py', kind='kit', template='narrated-short')
lesson('templates', 'Template catalog', 'Templates', 'Choose a runnable starter, edit its Python factory, and turn it into your own video.', [
section('Choose a starter', 'List the installed templates, then pick a fresh destination directory. init refuses to merge into an existing directory.', code('fc-kit list templates', 'bash'), dict(type='table', headers=['Template', 'Starting point', 'Defaults'], rows=[
    ['silent', 'Ten-second metric, comparison, and steps', 'Shorts · midnight · no audio'],
    ['explainer-short', 'Alias of the silent scaffold', 'Same files and defaults as silent'],
    ['narrated-short', 'Thirty-second synthetic narration demo', 'Shorts · midnight · sentence SRT cues'],
    ['whiteboard-basic', 'Two five-second drawing scenes', 'Landscape · whiteboard · no captions'],
])),
section('Create an editable project', 'Choose one command below. Each creates videos/main.py, facelesschamp.toml, an asset manifest, and local component/data folders. Generated files belong to you; upgrading the package does not rewrite them.', code('''
fc-kit init silent-video --template silent
fc-kit init explainer-video --template explainer-short
fc-kit init narrated-video --template narrated-short
fc-kit init board-video --template whiteboard-basic
''', 'bash')),
section('Call a template from Python', 'A callable template returns an ordinary editable Video. Save this factory in a silent project; adjust its content or append segments before returning it.', silent_template),
section('Use the narrated factory', 'Save this in a narrated-short project, which supplies the voiceover and word_cues manifest entries. The bundled sample is labeled SYNTHETIC DEMO AUDIO and uses sentence cues, not word-aligned subtitles.', narrated_template),
section('Replace the demonstration media', 'Replace the package resource entries in assets/manifest.json with paths to your own audio and SRT, remove the synthetic source metadata, and update the original cue indices in your factory. The narrated callable expects hook, comparison, and finish marker names. The runtime does not generate speech or download media.', link('Narration windows and captions →', '#framework-narration')),
section('Choose drawing recipes', 'whiteboard_basic(ctx, scenes=...) returns a Video with sequential stroke reveals. Use the next chapter for geometry, themes, timing, and narrated drawing scenes.', link('Build a whiteboard video →', '#whiteboard-videos')),
], guide='kit')

whiteboard = code('''
from facelesschamp_kit.blocks import (
    WhiteboardArrow, WhiteboardCircle, WhiteboardDrawing,
    WhiteboardLine, WhiteboardPath, WhiteboardRectangle,
)
from facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic


def build(ctx):
    return whiteboard_basic(
        ctx,
        theme=ctx.theme,
        draw_fraction=0.7,
        scenes=[
            WhiteboardScene(
                name="connect",
                duration=5,
                drawing=WhiteboardDrawing(
                    viewbox=(1400, 700),
                    drawings=(
                        WhiteboardCircle(center=(350, 350), radius=140, stroke_width=8),
                        WhiteboardArrow(start=(540, 350), end=(860, 350),
                                        color="#2563EB", stroke_width=8),
                        WhiteboardCircle(center=(1050, 350), radius=140, stroke_width=8),
                    ),
                ),
            ),
            WhiteboardScene(
                name="progress",
                duration=5,
                drawing=WhiteboardDrawing(
                    viewbox=(1400, 700),
                    drawings=(
                        WhiteboardRectangle(x=200, y=120, width=1000, height=460,
                                            stroke_width=8),
                        WhiteboardLine(start=(300, 480), end=(1100, 480),
                                       color="#64748B", stroke_width=6),
                        WhiteboardPath(points=((300, 440), (500, 400), (700, 320),
                                               (900, 300), (1100, 200)),
                                       color="#2563EB", stroke_width=10),
                    ),
                ),
            ),
        ],
    )
''', filename='kit_whiteboard.py', kind='kit', template='whiteboard-basic')
lesson('whiteboard-videos', 'Whiteboard videos', 'Templates', 'Draw an idea stroke by stroke, hold the finished diagram, then clear the board for the next scene.', [
section('Start a whiteboard project', 'This starter selects landscape, the whiteboard theme, and no captions. Replace videos/main.py with the downloadable factory below. The preview above shows the complete ten-second example.', code('''
fc-kit init my-board --template whiteboard-basic
cd my-board
fc-kit validate main
fc-kit frame main --time 4 -o output/frame.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main -o output/preview.mp4
''', 'bash')),
section('Build two drawing scenes', 'WhiteboardScene is an immutable recipe. Each scene has a unique name, a drawing, and either a positive duration or a narration cue window. This example uses no labels so the geometry carries the explanation.', whiteboard),
section('Choose paths and shapes', 'Import these immutable specifications from facelesschamp_kit.blocks. Each accepts color=None and stroke_width=5. Shapes are outlines without fills; open lines and paths have rounded ends.', dict(type='table', headers=['Specification', 'Geometry'], rows=[
    ['WhiteboardPath(points, closed=False)', 'At least two distinct points; three for a closed outline'],
    ['WhiteboardLine(start, end)', 'A straight stroke'],
    ['WhiteboardArrow(start, end, tip_size=18)', 'A stroke and arrowhead'],
    ['WhiteboardRectangle(x, y, width, height)', 'Top-left corner and dimensions'],
    ['WhiteboardCircle(center, radius)', 'Center and radius'],
])),
section('Fit the drawing to the canvas', 'WhiteboardDrawing(drawings, viewbox=(1000, 1000)) uses source coordinates from the top-left, with x right and y down. Keep all geometry inside the viewbox, including full circle outlines. Coordinates and dimensions must be finite, strokes positive, and arrowheads no longer than their line. The complete viewbox fits uniformly inside the safe area; changing formats preserves proportions and whitespace without rearranging the geometry.', code('''
# Edit these existing entries in facelesschamp.toml:
[videos.main]
factory = "videos.main:build"
format = "shorts"  # Use "landscape" for 16:9.
theme = "whiteboard"
captions = false
''', 'toml')),
section('Draw, hold, and clear', 'The default draw_fraction=0.7 divides the first 70% of each scene equally among its strokes, in order. Later strokes remain hidden until their start; the remaining 30% holds the completed board. Each new scene clears the previous drawing. Choose 0 < draw_fraction < 1. Omitted starts append scenes; explicit starts may leave blank gaps. Scenes must be chronological and cannot overlap.', note('WhiteboardDrawing used directly with segment.add() shows the completed drawing. The whiteboard_basic template schedules the reveals; its named children are stroke-0, stroke-1, and so on.')),
section('Add labels and style', 'An optional WhiteboardScene label fades in at the start and reserves the top 15% of the safe area. Labels wrap and shrink; unfit text produces TEXT_FIT. Captions reserve a separate bottom area. The factory defaults to WHITEBOARD and updates the context theme and canvas; pass theme=ctx.theme, as the example does, to honor project configuration.', code('''
from dataclasses import replace
from facelesschamp_kit.themes import WHITEBOARD

custom_theme = replace(WHITEBOARD, foreground="#17324D", accent="#F97316")
# In build(ctx), pass theme=custom_theme to whiteboard_basic.
# Add label="Connect ideas" to a WhiteboardScene to enable its label.
''')),
section('Attach your narration', 'Register your own audio and subtitle paths in assets/manifest.json. Supply audio, subtitles, and a nonempty marker mapping together. The marker values are original SRT cue indices, which need not be consecutive.', code('''
{
  "voice": {"type": "audio", "path": "assets/audio/voice.wav"},
  "words": {"type": "subtitle", "path": "assets/words.srt"}
}
''', 'json'), code('''
from facelesschamp_kit.blocks import WhiteboardCircle, WhiteboardDrawing
from facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic


def build(ctx):
    first_drawing = WhiteboardDrawing(
        drawings=(WhiteboardCircle(center=(500, 500), radius=200),))
    second_drawing = WhiteboardDrawing(
        drawings=(WhiteboardCircle(center=(300, 500), radius=150),
                  WhiteboardCircle(center=(700, 500), radius=150)))
    return whiteboard_basic(
        ctx,
        theme=ctx.theme,
        audio="voice",
        subtitles="words",
        markers={"opening": 7, "explanation": 19},
        captions=False,
        scenes=[
            WhiteboardScene("opening", first_drawing,
                            cues=("opening", "explanation")),
            WhiteboardScene("explanation", second_drawing,
                            cues=("explanation", None)),
        ],
    )
'''), note('This factory requires your own media and valid cue indices; replace its simple circles with your own drawings. Audio starts at master time zero, preserving leading silence. A gap before the first cue shows an empty board; None ends the last window at the audio duration. Do not combine cues with start or duration in one scene. The last board holds through an attached audio tail. captions=None inherits project configuration.')),
section('Extend the returned video', 'The returned Video supports normal segments and overlays. Add a closing segment or target drawing children with core animations. The implemented template supports geometry outlines. Hand overlays, image tracing, handwriting fonts, media generation, and boards that persist across recipe scenes are future capabilities.', link('Create your own reusable blocks →', '#custom-blocks')),
], 'whiteboard', guide='kit')

lesson('kit-preview-and-export', 'Preview & export', 'Ship your video', 'Validate the project, inspect its layout, and export using the configured profiles.', [
section('Validate before rendering', 'Validation checks every export profile and writes reports under .fc-kit/reports/. inspect summarizes the built timeline and assets.', code('''
fc-kit validate main
fc-kit inspect main --json
''', 'bash')),
section('Inspect frames and scenes', 'Frame times must lie inside the video duration. The storyboard samples the project; use a segment ID from inspect to focus a preview.', code('''
fc-kit frame main --time 1 -o output/frame.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main --start 0 --end 3 -o output/excerpt.mp4
''', 'bash')),
section('Preview and export', 'preview defaults to the first ten seconds; render exports the complete video with the final profile. Output paths resolve from the invoking directory. Add --overwrite to deliberately replace an existing export.', code('''
fc-kit preview main -o output/preview.mp4
fc-kit render main -o output/final.mp4
''', 'bash'), note('A successful still or short preview verifies that sample. Inspect representative frames and completely decode the final export before treating the full video as verified.')),
], guide='kit')
lesson('kit-troubleshooting', 'Troubleshooting', 'Ship your video', 'Use diagnostics and short previews to resolve project, template, and export errors.', [
section('Common fixes', 'Start with fc-kit doctor and fc-kit validate main. Errors include the relevant project or segment context.', dict(type='table', headers=['Symptom', 'Fix'], rows=[
    ['FFmpeg / ffprobe / libx264 missing', 'Install FFmpeg and check PATH with fc-kit doctor.'],
    ['Destination already exists', 'Use a new directory; init does not merge projects.'],
    ['TEXT_FIT / layout overflow', 'Shorten labels, enlarge bounds, or split the scene.'],
    ['Missing asset / final placeholder', 'Provide the actual manifest asset; final exports reject placeholders by default.'],
    ['Unknown narration marker', 'Use an existing original SRT cue index and the correct marker name.'],
    ['WHITEBOARD_TIMING', 'Keep scenes chronological and nonoverlapping, with 0 < draw_fraction < 1.'],
    ['Invalid whiteboard geometry', 'Keep shapes inside the viewbox with finite dimensions and positive strokes.'],
    ['Whiteboard appears immediately', 'Use whiteboard_basic for animation; the standalone block displays the completed drawing.'],
    ['Wrong whiteboard colors', 'Select theme="whiteboard" in the project when passing theme=ctx.theme.'],
    ['Output already exists', 'Choose another path or explicitly add --overwrite.'],
])),
section('Bound the work', 'Use a frame, a storyboard, and a short preview before raising resolution or frame rate. The kit uses the core CPU Pillow renderer and FFmpeg encoder.'),
section('Keep the current scope clear', 'The framework is a local 0.1.0rc1 release candidate. It consumes local assets and bundled demonstration media; it neither generates speech nor downloads media.', link('Core rendering and animation guide →', 'index.html')),
], guide='kit')

core_lessons = [item for item in lessons if item['guide'] == 'core']
kit_lessons = {item['id']: item for item in lessons if item['guide'] == 'kit'}
for item in lessons:
    if item['id'] in ('framework-quickstart', 'project-configuration'):
        item['group'] = 'Start here'
    elif item['id'] in ('blocks-and-themes', 'custom-blocks', 'framework-narration'):
        item['group'] = 'Framework fundamentals'
# Keep chapter groups contiguous in the sidebar and reading order.
kit_order = ['framework-quickstart', 'kit-installation', 'project-configuration',
             'blocks-and-themes', 'custom-blocks', 'framework-narration', 'templates',
             'whiteboard-videos', 'kit-preview-and-export', 'kit-troubleshooting']
assert set(kit_order) == set(kit_lessons)
lessons = core_lessons + [kit_lessons[key] for key in kit_order]
guides = {
    'core': dict(title='Faceless Champ Core Guide', label='Core library', file='index.html',
                 version='0.1.0', kind='PYTHON LIBRARY', home='hello-world',
                 introduction='Create animated videos with Python scenes, components, and a precise timeline.'),
    'kit': dict(title='facelesschamp-kit Guide', label='Kit framework', file='kit.html',
                version='0.1.0rc1', kind='FRAMEWORK', home='framework-quickstart',
                introduction='Build structured video projects with reusable blocks, editable templates, and narration cues.'),
}
(DIST / 'content.json').write_text(json.dumps(dict(lessons=lessons, guides=guides), indent=2) + '\n')
print(f'Generated {len(core_lessons)} core and {len(kit_lessons)} kit chapters, '
      f'with {len(list(EXAMPLES.glob("*.py")))} downloadable examples.')
