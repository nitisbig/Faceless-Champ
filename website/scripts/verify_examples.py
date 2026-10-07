"""Build every downloadable guide example and render selected real previews."""
import ast
import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'facelesschamp-kit/src')]
from faceless_champ import PillowRenderer, save_frame
from facelesschamp_kit import Project
from facelesschamp_kit.scaffold import init_project

DIST = REPO / 'website/dist'
content = json.loads((DIST / 'content.json').read_text())
previews = {'hello.py':'hello', 'text_shapes.py':'text-shapes', 'charts.py':'charts',
            'properties.py':'properties', 'masks.py':'masks', 'indicators.py':'indicators',
            'kit_main.py':'kit'}
render_previews = '--render' in sys.argv
report = {'chapters':len(content['lessons']), 'python_snippets':0, 'examples':[]}
for lesson in content['lessons']:
    for section in lesson['sections']:
        for block in section['blocks']:
            if block['type'] != 'code' or block['language'] != 'python':
                continue
            ast.parse(block['code'])
            report['python_snippets'] += 1
            if not block.get('filename'):
                continue
            filename = block['filename']
            path = DIST / 'examples' / filename
            assert path.read_text() == block['code'], filename
            with tempfile.TemporaryDirectory(prefix='fc-guide-check-') as temporary:
                if block['kind'] == 'kit':
                    project_path = Path(temporary) / 'video'
                    init_project(project_path)
                    (project_path / 'videos/main.py').write_text(block['code'])
                    project = Project(project_path)
                    project.validate('main')
                    node = project.build('main').composition
                else:
                    namespace = runpy.run_path(str(path))
                    node = namespace[block['target']]
                    if isinstance(node,type):
                        node = node()
                    if hasattr(node, "build"):
                        node.build()
                size = (360,640) if block['kind']=='kit' else (270,480) if filename=='portrait.py' else (640,360)
                t = min(1.5, node.duration / 2)
                renderer = PillowRenderer(1)
                for moment in (0, t, max(0,node.duration-0.05)):
                    frame = renderer.frame(node,moment,size)
                    assert frame.size==size
                entry = {'file':filename,'duration':node.duration,'sampled_frames':3}
                if filename in previews and render_previews:
                    name=previews[filename]
                    save_frame(node,t,DIST/'assets'/f'{name}.png',size=size,overwrite=True)
                    node.render(DIST/'assets'/f'{name}.mp4',width=size[0],height=size[1],fps=15,
                                antialias=1,preset='veryfast',overwrite=True,
                                **({'end_time':3} if block['kind']=='kit' else {}))
                    subprocess.run(['ffmpeg','-v','error','-i',str(DIST/'assets'/f'{name}.mp4'),
                                    '-f','null','-'],check=True,capture_output=True)
                    probe=subprocess.run(['ffprobe','-v','error','-show_entries',
                                          'format=duration:stream=codec_name,width,height',
                                          '-of','json',str(DIST/'assets'/f'{name}.mp4')],
                                         check=True,capture_output=True,text=True)
                    entry['media']=json.loads(probe.stdout)
                report['examples'].append(entry)
                print(f'PASS {filename}: {node.duration:g}s',flush=True)
(REPO/'website/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(f"Verified {report['python_snippets']} Python snippets and {len(report['examples'])} complete examples.")
