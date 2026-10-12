"""Check both guides, build examples and starters, and optionally render their previews."""
import ast
import json
import re
import runpy
import subprocess
import sys
import tempfile
import tomllib
import os
from datetime import datetime, timezone
from unittest.mock import patch
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'facelesschamp-kit/src')]
from faceless_champ import PillowRenderer, save_frame
from facelesschamp_kit import Project
from facelesschamp_kit.cli import CATALOG
from facelesschamp_kit.scaffold import init_project

DIST = REPO / 'website/dist'
content = json.loads((DIST / 'content.json').read_text())
previews = {'hello.py': 'hello', 'text_shapes.py': 'text-shapes', 'charts.py': 'charts',
            'properties.py': 'properties', 'masks.py': 'masks', 'indicators.py': 'indicators',
            'kit_main.py': 'kit', 'kit_whiteboard.py': 'whiteboard',
            'coding.py': 'coding', 'playground.py': 'playground',
            'chess.py': 'chess', 'flow.py': 'flow'}
render_previews = '--render' in sys.argv
report = {'verified_at': datetime.now(timezone.utc).isoformat(),
          'preview_background': '#000000', 'guides': {}, 'chapters': len(content['lessons']), 'python_snippets': 0,
          'examples': [], 'starters': [], 'links_checked': 0}
lessons = {lesson['id']: lesson for lesson in content['lessons']}
assert len(lessons) == len(content['lessons']), 'Duplicate chapter ID'
# Checkpoint workers must import the same source checkout as this verifier.
os.environ['PYTHONPATH'] = os.pathsep.join(sys.path[:2] + [os.environ.get('PYTHONPATH', '')])
real_popen = subprocess.Popen


def playback_process(args, *positional, **keywords):
    # Encoding/probing is allowed; checkpoint Python and browser launches are not.
    assert not keywords.get('shell'), 'Playback unexpectedly used a shell'
    assert Path(str(args[0])).name in {'ffmpeg', 'ffprobe'}, f'Playback launched {args[0]}'
    return real_popen(args, *positional, **keywords)


def replay_project(project):
    with patch('subprocess.Popen', playback_process):
        project.validate('main')
        node = project.build('main').composition
        sample(node, [0, node.duration / 2, node.duration - .05])
    return node


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def check_link(href, current_guide):
    parts = urlsplit(href)
    if parts.scheme:
        return
    if parts.path:
        assert (DIST / unquote(parts.path)).is_file(), href
        target_guide = next((key for key, value in content['guides'].items()
                             if value['file'] == parts.path), None)
    else:
        target_guide = current_guide
    if parts.fragment:
        chapter, _, section = parts.fragment.partition('/')
        assert chapter in lessons, href
        assert lessons[chapter]['guide'] == target_guide, href
        if section:
            assert section in {slug(item['title']) for item in lessons[chapter]['sections']}, href
    report['links_checked'] += 1


def preview_size(node):
    scale = 640 / max(node.canvas.width, node.canvas.height)
    return tuple(max(2, round(value * scale / 2) * 2)
                 for value in (node.canvas.width, node.canvas.height))


def sample(node, times):
    size = preview_size(node)
    renderer = PillowRenderer(1)
    for moment in times:
        assert 0 <= moment < node.duration
        assert renderer.frame(node, moment, size).size == size
    return size


template_table = next(block for section in lessons['templates']['sections']
                      for block in section['blocks'] if block['type'] == 'table')
assert {row[0] for row in template_table['rows']} == set(CATALOG['templates'])

for key, guide in content['guides'].items():
    assert lessons[guide['home']]['guide'] == key
    page = (DIST / guide['file']).read_text()
    assert f'data-guide="{key}"' in page
    manifest = REPO / ('pyproject.toml' if key == 'core' else 'facelesschamp-kit/pyproject.toml')
    assert guide['version'] == tomllib.loads(manifest.read_text())['project']['version']
    assert f'{guide["label"]} v{guide["version"]}' in page
    assert all(f'href="{other["file"]}"' in page for other in content['guides'].values())
    report['guides'][key] = {'page': guide['file'], 'version': guide['version'], 'chapters': sum(
        lesson['guide'] == key for lesson in lessons.values())}

for lesson in content['lessons']:
    assert lesson['guide'] in content['guides']
    section_ids = [slug(section['title']) for section in lesson['sections']]
    assert len(section_ids) == len(set(section_ids)), lesson['id']
    if lesson['preview'] and not render_previews:
        for extension in ('png', 'mp4'):
            assert (DIST / 'assets' / f'{lesson["preview"]}.{extension}').is_file()
    for section in lesson['sections']:
        for block in section['blocks']:
            if block['type'] == 'link':
                check_link(block['href'], lesson['guide'])
            if block['type'] != 'code' or block['language'] != 'python':
                continue
            tree = ast.parse(block['code'])
            compile(tree, f"{lesson['id']}/{section['title']}", 'exec')
            report['python_snippets'] += 1
            if not block.get('filename'):
                continue
            filename = block['filename']
            path = DIST / 'examples' / filename
            assert path.read_text() == block['code'], filename
            check_link(f'examples/{filename}', lesson['guide'])
            with tempfile.TemporaryDirectory(prefix='fc-guide-check-') as temporary:
                preparation = None
                if filename in {'html_video.py', 'kit_web.py'}:
                    from PIL import Image
                    from faceless_champ import Canvas, Scene
                    from facelesschamp_kit.context import BuildContext
                    asset = Path(temporary) / 'capture'
                    asset.mkdir()
                    Image.new('RGB', (144, 90), '#345678').save(asset / '00000000.png')
                    (asset / 'manifest.json').write_text(json.dumps({
                        'schema': 1, 'fps': 1, 'duration': 1, 'viewport': [144, 90],
                        'frames': {'0': {'geometry': {}, 'cursor': [0, 0], 'clicks': []}}}))
                    namespace = runpy.run_path(str(path))
                    if filename == 'html_video.py':
                        node = namespace['build_scene'](asset)
                    else:
                        ctx = BuildContext(Path(temporary), canvas=Canvas(1920, 1080))
                        node = Scene(ctx.canvas)
                        node.add(namespace['walkthrough'](asset).compose(ctx, ctx.bounds).root)
                        node.wait(1)
                    preparation = {'verification': 'synthetic capture playback only; no browser interaction claim'}
                elif block['kind'] == 'kit':
                    project_path = Path(temporary) / 'video'
                    init_project(project_path, block['template'])
                    (project_path / 'videos/main.py').write_text(block['code'])
                    project = Project(project_path)
                    if block.get('preparation'):
                        preparation = project.prepare('main')['prepared_assets']
                    node = replay_project(project)
                elif block.get('preparation') == 'playground':
                    from faceless_champ import PreparedPlayground, prepare_playground
                    with patch('subprocess.Popen', playback_process):
                        namespace = runpy.run_path(str(path))
                    asset = prepare_playground(namespace['script'](), cache_dir=Path(temporary) / 'prepared')
                    with patch('subprocess.Popen', playback_process):
                        node = namespace['build_scene'](PreparedPlayground(asset.directory))
                    preparation = {'fingerprint': asset.fingerprint, 'checkpoint_execution': 'explicit',
                                   'playback_without_execution': True}
                else:
                    namespace = runpy.run_path(str(path))
                    node = namespace[block['target']]
                    if isinstance(node, type):
                        node = node()
                    if hasattr(node, 'build'):
                        node.build()
                times = ([0, 0.6, 2.5, 4, 5, 6.2, 9.5] if filename == 'kit_whiteboard.py'
                         else [0, min(1.5, node.duration / 2), max(0, node.duration - 0.05)])
                with patch('subprocess.Popen', playback_process):
                    size = sample(node, times)
                entry = {'file': filename, 'guide': lesson['guide'], 'duration': node.duration,
                         'sampled_frames': len(times), 'sample_times': times, 'size': size}
                if preparation is not None:
                    entry['preparation'] = preparation
                if block.get('preparation'):
                    entry['playback_without_execution'] = True
                if block['kind'] == 'kit':
                    entry['template'] = block['template']
                if filename == 'kit_whiteboard.py':
                    project.config['videos']['main']['format'] = 'shorts'
                    project.validate('main')
                    portrait = project.build('main').composition
                    entry['portrait_size'] = sample(portrait, times)
                    entry['formats_checked'] = ['landscape', 'shorts']
                if filename in previews and render_previews:
                    name = previews[filename]
                    assert node.canvas.bg in {'#000000', 'black'}, (filename, node.canvas.bg)
                    poster_time = {'playground.py': 4.4, 'flow.py': 4.2, 'chess.py': 4.7,
                                   'coding.py': 3, 'kit_whiteboard.py': 4}.get(filename, times[1])
                    save_frame(node, poster_time, DIST / 'assets' / f'{name}.png', size=size, overwrite=True)
                    # The original kit overview deliberately shows only its three-second hook.
                    end = 3 if filename == 'kit_main.py' else node.duration
                    with patch('subprocess.Popen', playback_process):
                        node.render(DIST / 'assets' / f'{name}.mp4', width=size[0], height=size[1], fps=15,
                                    antialias=1, preset='veryfast', overwrite=True, end_time=end)
                    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(DIST / 'assets' / f'{name}.mp4'),
                                    '-f', 'null', '-'], check=True, capture_output=True)
                    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                            'format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames',
                                            '-of', 'json', str(DIST / 'assets' / f'{name}.mp4')],
                                           check=True, capture_output=True, text=True)
                    entry['media'] = json.loads(probe.stdout)
                    entry['fully_decoded'] = True
                    actual = float(entry['media']['format']['duration'])
                    assert abs(actual - end) <= 1 / 15 + 0.01, (filename, actual, end)
                    stream = entry['media']['streams'][0]
                    assert (stream['width'], stream['height']) == size
                    assert stream['r_frame_rate'] == '15/1'
                    entry['preview_duration'] = end
                    entry['preview_background'] = '#000000'
                report['examples'].append(entry)
                print(f'PASS {filename}: {node.duration:g}s', flush=True)

for template in CATALOG['templates']:
    with tempfile.TemporaryDirectory(prefix='fc-guide-starter-') as temporary:
        root = init_project(Path(temporary) / 'video', template)
        project = Project(root)
        prepared = project.prepare('main')['prepared_assets'] if template.startswith('coding-') else []
        node = replay_project(project)
        size = sample(node, [0, node.duration / 2, node.duration - 0.05])
        report['starters'].append({'template': template, 'duration': node.duration,
                                   'size': size, 'validated': True, 'sampled_frames': 3,
                                   'prepared_assets': prepared, 'playback_without_execution': True})
        print(f'PASS starter {template}', flush=True)

report['previews'] = []
for filename, name in previews.items():
    entry = next(item for item in report['examples'] if item['file'] == filename)
    path = DIST / 'assets' / f'{name}.mp4'
    if not entry.get('fully_decoded'):
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'],
                       check=True, capture_output=True)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames',
                            '-of', 'json', str(path)], check=True, capture_output=True, text=True)
    media = json.loads(probe.stdout)
    stream = media['streams'][0]
    expected = 3 if filename == 'kit_main.py' else entry['duration']
    assert abs(float(media['format']['duration']) - expected) <= 1 / 15 + .01
    assert (stream['width'], stream['height']) == tuple(entry['size'])
    assert stream['r_frame_rate'] == '15/1'
    assert stream['codec_name'] == 'h264'
    report['previews'].append({'name': name, 'media': media, 'fully_decoded': True,
                               'rendered_this_run': render_previews, 'background': '#000000'})

(REPO / 'website/verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(f"Verified {report['chapters']} chapters, {report['python_snippets']} Python snippets, "
      f"{len(report['examples'])} complete examples, and {len(report['starters'])} starters.")
