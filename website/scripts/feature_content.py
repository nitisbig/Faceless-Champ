"""Recent feature chapters; examples only execute preparation from explicit runners."""

CODING = '''from faceless_champ import Canvas, CodeReveal, CodingChamp, Scene

class CodeDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1280, 720, "#080E1B"))

    def construct(self):
        panel = CodingChamp(
            "def square(x):\\n    return x * x\\n\\nprint(square(7))",
            language="python", filename="square.py", theme="midnight",
            width=1080, height=520, font_size=40, position=(640, 360),
            reveal_mode="block", block_ends=(2, 4), highlighted_lines=(2,),
        )
        self.play(CodeReveal(panel, end=.5), run_time=1)
        self.wait(.5)
        self.play(CodeReveal(panel, start=.5), run_time=1)
        self.wait(1)
'''

PLAYGROUND = '''import argparse
from faceless_champ import (
    Canvas, CanvasItem, CodeCheckpoint, CodeEditor, PlaygroundCanvas,
    PlaygroundOutput, PlaygroundScript, PreparedPlayground, Scene,
    ValueBinding, prepare_playground,
)

SOURCE = "from faceless_champ.playground import (\\n    runtime as pg,\\n)\\nx = VALUE\\nanswer = x * x\\npg.emit('answer', answer)\\nprint(answer)\\n"

def script():
    return PlaygroundScript([
        CodeCheckpoint("first", {"square.py": SOURCE.replace("VALUE", "6")},
                       "square.py", "square.py", 0, 1, 1),
        CodeCheckpoint("second", {"square.py": SOURCE.replace("VALUE", "7")},
                       "square.py", "square.py", 2.5, 4, 4),
    ], duration=6, mode="backend",
       items=[CanvasItem("answer", "variable", "Answer")],
       bindings=[ValueBinding("answer", "answer")])

def build_scene(asset):
    scene = Scene(Canvas(1280, 720, "#0B1020"))
    scene.add(CodeEditor(asset.script, width=780, height=600,
                         font_size=22, position=(420, 360)))
    scene.add(PlaygroundCanvas(asset, width=400, height=380, position=(1050, 250)))
    scene.add(PlaygroundOutput(asset, width=400, height=180, position=(1050, 570)))
    scene.wait(asset.script.duration)
    return scene

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true",
                        help="Execute trusted checkpoints explicitly")
    parser.add_argument("--cache", default=".playground-cache")
    parser.add_argument("--asset", help="Prepared directory for browser-free replay")
    parser.add_argument("--output", default="output/playground.mp4")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        asset = prepare_playground(script(), cache_dir=args.cache)
        print("Prepared:", asset.directory)
    elif args.asset:
        asset = PreparedPlayground(args.asset)
    else:
        parser.error("Use --prepare or --asset PATH")
    build_scene(asset).render(args.output, width=640, height=360, fps=15,
                             antialias=1, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
'''

CHESS = '''from faceless_champ import Canvas, ChessChamp, ChessScript, ChessTheme, Scene

class ChessDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1280, 720, "#171E1A"))

    def construct(self):
        script = ChessScript.from_dict({
            "schema_version": 1, "duration": 6,
            "players": {"white": "White", "black": "Black"},
            "moves": [
                {"at": 1, "duration": .5, "uci": "e2e4"},
                {"at": 2.5, "duration": .5, "uci": "d7d5"},
                {"at": 4, "duration": .5, "uci": "e4d5"},
            ],
            "annotations": [
                {"type": "text", "at": 0, "duration": 6,
                 "text": "e4 / d5 / exd5"},
                {"type": "highlight", "at": 3, "duration": 1,
                 "squares": ["e4", "d5"]},
            ],
        })
        self.add(ChessChamp(script, theme=ChessTheme(background="#000000"), width=1280, height=720, position=(640, 360)))
        self.wait(script.duration)
'''

FLOW = '''from faceless_champ import Canvas, FlowChamp, FlowTheme, Scene
from faceless_champ.flow.examples import recipe

class FlowDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1200, 675, "#0B1020"))

    def construct(self):
        graph, script = recipe("system")
        diagram = FlowChamp(graph, script, width=1200, height=675,
                            position=(600, 337.5),
                            theme=FlowTheme(background="#000000", stroke="#8996AD"))
        self.add(diagram)
        self.wait(6)
'''


def add_features(root, code, section, note, link, lesson):
    lesson('codingchamp', 'CodingChamp editors', 'Library fundamentals',
           'Reveal syntax-colored code without changing its measured layout.', [
        section('Install and reveal code', 'Install the coding extra for Pygments. The default bundled monospace font preserves indentation. Plain language="text" needs no extra.',
                code(CODING, filename='coding.py', target='CodeDemo')),
        section('Choose a reveal', 'CodeReveal uses normalized progress. typewriter reveals characters, word reveals whitespace-separated words, and block uses increasing inclusive line numbers ending at the final line. All modes preserve source whitespace.'),
        section('Style and fit', 'CodeTheme.named supports midnight, ocean, and paper. Customize immutable themes with dataclasses.replace. Use font_size, highlighted_lines, first_line, and panel dimensions; oversized fixed code fails rather than wrapping or executing.'),
        section('Animate edits and results', 'For changing source revisions, real checkpoint output, and explicit result bindings, use prepared playgrounds.', link('Coding playgrounds →', '#coding-playgrounds')),
    ], 'coding')

    playground = code(PLAYGROUND, filename='playground.py', target='build_scene')
    playground['command'] = 'python playground.py --prepare --output output/playground.mp4'
    playground['preparation'] = 'playground'
    lesson('coding-playgrounds', 'Coding playgrounds', 'Library fundamentals',
           'Animate complete source revisions beside explicitly bound results.', [
        section('Prepare then replay', 'Install the playground extra. This six-second example executes two complete Python checkpoints only when --prepare is requested. Importing the file has no execution side effects.', playground),
        section('Use saved results', 'The runner prints its prepared directory. Reopen it to render without executing checkpoints.', code('python playground.py --asset PATH_TO_PREPARED_DIRECTORY --output output/replay.mp4', 'bash')),
        section('Bind meaning explicitly', 'ValueBinding maps emitted keys to authored canvas items. EventBinding maps named emitted events to highlights, travelling events, or tensor cells. Concept mode supports cars/objects; backend mode supports flows, variables, collections, vectors, and matrices. Intermediate edits never execute.'),
        section('Prepare web revisions', 'Web checkpoints contain complete HTML/CSS/JavaScript revisions and optional WebScript interactions. Install Chromium explicitly, prepare at the export FPS, and replay captured pixels. No backend or external requests are required.', link('HTML capture →', '#html-to-video')),
        section('Handle preparation errors', 'Source, binding, timing, input, or preparation-setting changes require preparation again. Missing prepared assets raise PLAYGROUND_UNPREPARED. Timeout, output limits, invalid bindings, and unexpected execution failures stop preparation; no incomplete asset is published.', note('Preparation executes trusted local code with your OS permissions. Subprocesses are not a security sandbox. A successful preparation does not verify a video export.')),
        section('Use structured projects', 'Choose coding-concept, coding-backend, or coding-web and prepare explicitly.', link('Kit coding playgrounds →', 'kit.html#kit-coding-playgrounds')),
    ], 'playground')

    lesson('chesschamp', 'ChessChamp', 'Library fundamentals',
           'Render legal timed games with bundled board artwork and annotations.', [
        section('Render legal moves', 'Install the chess extra. ChessScript validates every move before rendering; the bundled PNG artwork works offline.', code(CHESS, filename='chess.py', target='ChessDemo')),
        section('Author JSON or import PGN', 'ChessScript.from_json reads required schema_version=1, duration, timed UCI moves, and optional annotations. from_dict accepts the same document. from_pgn imports SAN mainlines into timed moves; to_dict exports the JSON contract. Legal move validation includes a custom starting FEN when supplied.'),
        section('Choose artwork and perspective', 'ChessAssets.bundled provides the board and twelve piece cutouts. ChessAssets(directory, board_grid=...) accepts a custom set; JSON assets.directory resolves relative to its document. orientation="black" rotates the board while pieces remain upright.'),
        section('Narration and scope', 'Core callers attach existing audio once at master zero. ChessChamp supplies visuals and rules, without interactive play or engine evaluation.', link('Kit chess tutorials →', 'kit.html#kit-chesschamp')),
    ], 'chess')

    lesson('archchamp', 'ArchChamp technical 3D', 'Library fundamentals',
           'Explain geometry through named parts, camera motion, sections and dimensions.', [
        section('Explore an assembly', 'This original silent 12-second fixture shows transparent geometry, exploded parts and a moving section. PyVista is a required core dependency.',
                code((root.parent / 'examples/archchamp.py').read_text(), filename='archchamp.py', target='build_scene')),
        section('Choose a concept', 'Wireframe, topology, transparent/X-ray, clay, blueprint, point cloud, isometric, supplied heatmap/vector fields and voxel views share one viewport. Import local meshes or generate parametric geometry with Python. CAD modeling and simulation solving remain external.'),
        section('Animate and annotate', 'ArchScript schedules camera, named part, explosion, highlight and section actions. Labels and dimensions follow world or part-local anchors with explicit model units. Source offsets and random seeking preserve the authored clock.'),
        section('Compose and manage resources', 'Use normal scenes, groups, masks and composition. Renderer-owned offscreen sessions reuse actors; use a renderer context manager for manual frames.', link('Kit ArchCanvas →', 'kit.html#kit-archchamp')),
    ], 'archchamp')

    lesson('kit-archchamp', 'Technical 3D designs', 'Framework fundamentals',
           'Fit technical models into reusable authoring blocks and agent recipes.', [
        section('Start a silent design', 'The archchamp starter contains a small original assembly. ArchCanvas exposes model; ArchScript controls individual 3D parts.',
                code((root.parent / 'facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py').read_text(), filename='kit_archchamp.py', kind='kit', template='archchamp')),
        section('Track models', 'Register files as mesh assets and resolve through ctx.assets.mesh. Geometry hashes, model checksums, and PyVista/VTK versions enter reports and agent evidence fingerprints.'),
        section('Use external libraries', 'Declare project tools with uv add in pyproject.toml and install with uv sync. Project.dependencies and doctor check installed distribution versions; rendering never installs packages.'),
        section('Author structured plans', 'The arch-design recipe accepts a design object with named parts, registered meshes or primitives, styles, camera, script, labels, dimensions and units.', link('Core ArchChamp →', 'index.html#archchamp')),
    ], guide='kit')

    lesson('flowchamp', 'FlowChamp diagrams', 'Library fundamentals',
           'Draw workflows, systems, networks, idea maps, and circuits on an authored clock.', [
        section('Animate a system', 'FlowChamp uses core Pillow rendering with no optional extra. This recipe draws the graph, sends packets, and highlights the service.', code(FLOW, filename='flow.py', target='FlowDemo')),
        section('Author graphs and actions', 'FlowGraph contains stable FlowNode, FlowPort, and FlowEdge IDs. Define ports, labels, straight/orthogonal routes, and arrows; FlowScript schedules draws, signals, reveals, highlights, moves, scales, and rotations. Python and from_json/to_dict support authored documents.'),
        section('Style and inspect', 'FlowTheme.stroke separates neutral structure from accent signals; stroke=None preserves legacy accent outlines. diagnostics_at(time) reports sampled visible bounds and label overlaps on the script clock. Sampling cannot prove all intermediate frames are collision-free.'),
        section('Compose and seek', 'Use source_start for excerpts and ordinary transforms, groups, opacity, and masks. Playback is time-seekable; final states hold.', link('Kit FlowCanvas →', 'kit.html#kit-flowchamp')),
    ], 'flow')

    kit_playground = code((root.parent / 'facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py').read_text(),
                          filename='kit_playground.py', kind='kit', template='coding-concept')
    kit_playground['command'] = 'fc-kit prepare main\nfc-kit preview main -o output/preview.mp4'
    kit_playground['preparation'] = 'playground'
    lesson('kit-coding-playgrounds', 'Coding playgrounds', 'Framework fundamentals',
           'Prepare code revisions explicitly, then compose replayable editor and result blocks.', [
        section('Create and prepare', 'Choose coding-concept, coding-backend, or coding-web. Web preparation additionally needs Chromium.', code('fc-kit init lesson --template coding-concept\ncd lesson\nfc-kit prepare main\nfc-kit validate main\nfc-kit preview main -o output/preview.mp4', 'bash')),
        section('Edit a complete lesson', 'Save the factory below in the concept scaffold, then prepare again. Two independent cars receive explicitly bound values.', kit_playground),
        section('Use blocks and named children', 'CodeEditor and CodingPlayground expose editor, canvas, and optional output. coding_playground(ctx, script, ...) supports side/stacked layouts, code_ratio, start, and narration cue windows. ctx.playground declares a prepared dependency.'),
        section('Keep execution explicit', 'Project.prepare / fc-kit prepare are the checkpoint execution boundary. Use --refresh to rerun matching cached inputs. build, validate, inspect, frame, storyboard, preview, and render replay prepared assets. Reports include prepared_assets fingerprints and paths.', link('Core checkpoint and binding guide →', 'index.html#coding-playgrounds')),
    ], guide='kit')

    lesson('kit-chesschamp', 'Chess tutorials', 'Framework fundamentals',
           'Use a legal timed data.json game in an editable kit project.', [
        section('Create a chess project', 'Install matching sources with the chess extra; edit the required scaffold data.json.', code('python -m pip install -e ".[chess]" -e "./facelesschamp-kit[chess]"\nfc-kit init chess-lesson --template chesschamp\ncd chess-lesson\nfc-kit validate main\nfc-kit preview main -o output/preview.mp4', 'bash')),
        section('Compose a reusable board', 'The scaffold supplies data.json. templates.chesschamp returns an editable Video; ChessBoard exposes the board child and accepts theme, assets, and source_start.', code('from facelesschamp_kit.templates import chesschamp\n\ndef build(ctx):\n    return chesschamp(ctx, data="data.json")', filename='kit_chess.py', kind='kit', template='chesschamp')),
        section('Attach existing narration', 'JSON narration.audio names a registered kit audio asset. Audio-only narration is supported; cue methods and captions require subtitles. Audio stays on the master clock.', link('Core moves, PGN, and artwork →', 'index.html#chesschamp')),
    ], guide='kit')

    lesson('kit-flowchamp', 'Flow diagrams', 'Framework fundamentals',
           'Fit scripted graphs into structured video layouts and narration windows.', [
        section('Start or compose', 'fc-kit init my-flow --template flowchamp creates an editable recipe project. FlowCanvas inherits kit fonts and colors.', code((root.parent / 'facelesschamp-kit/examples/flowchamp.py').read_text(), filename='kit_flow.py', kind='kit', template='flowchamp')),
        section('Target graph elements', 'Use the diagram handle for whole-viewport kit motion and stable FlowScript IDs for individual nodes/connections. FlowCanvas supports viewport and source_start; scripts must fit their placement lifetime.'),
        section('Time events to narration', 'Attach existing audio/SRT once and use Segment.cue_time(original_index) to translate original source cues into local FlowScript action times.'),
        section('Inspect timed diagnostics', 'Neutral outlines inherit Theme.muted; packets/highlights use accent. FLOW_BOUNDS, FLOW_OVERLAP, and FLOW_LABEL_OVERLAP warnings include segment, placement, script_time, and master source_time. Compiler samples action boundaries, midpoints, and excerpt endpoints.', link('Core graph authoring →', 'index.html#flowchamp')),
    ], guide='kit')

HTML = '''import argparse
import tempfile
from pathlib import Path
from faceless_champ import Canvas, Scene
from faceless_champ.web import HtmlClip, HtmlPage, WebCapture, WebScript, capture_html

PAGE = """<!doctype html><meta charset="utf-8">
<style>body { background: black; color: white; font: 36px sans-serif;
margin: 80px; } button { font: inherit; padding: 20px; }</style>
<h1>A prepared local page</h1><button id="count">Count: 0</button>
<script>let count=0; document.querySelector('#count').onclick = event => {
event.target.textContent = 'Count: ' + (++count); };</script>"""

def build_scene(capture_directory):
    capture = WebCapture(capture_directory)
    scene = Scene(Canvas(1920, 1080, "#000000"))
    scene.add(HtmlClip(capture, width=1440, height=900, position=(960, 540)))
    scene.wait(capture.duration)
    return scene

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--capture", help="Existing prepared capture directory")
    parser.add_argument("--cache", default=".web-cache")
    parser.add_argument("--output", default="output/html-tour.mp4")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        with tempfile.TemporaryDirectory(prefix="fc-local-page-") as temporary:
            path = Path(temporary) / "index.html"
            path.write_text(PAGE)
            script = WebScript(4).click("#count", at=1).click("#count", at=2)
            script.track("#count")
            capture = capture_html(HtmlPage(path, viewport=(1440, 900)), script,
                                   fps=15, cache_dir=args.cache)
        directory = capture.directory
        print("Prepared:", directory)
    elif args.capture:
        directory = args.capture
    else:
        parser.error("Use --prepare or --capture PATH")
    build_scene(directory).render(args.output, width=640, height=360, fps=15,
                                  antialias=1, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
'''
