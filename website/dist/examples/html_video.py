from faceless_champ import Canvas, Scene
from faceless_champ.web import HtmlClip, WebCapture

def build_scene(capture_directory):
    capture = WebCapture(capture_directory)
    scene = Scene(Canvas(1920, 1080, '#101827'))
    scene.add(HtmlClip(capture, width=1440, height=900, position=(960, 540)))
    scene.wait(capture.duration)
    return scene
