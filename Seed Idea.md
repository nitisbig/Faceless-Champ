# FacelessChamp

faceless video maker library in python 

### Core Engine

- Canvas
- Scene
- Grid
- Animate
- Text
- Node
- Object
- Position, timing, size

**Canvas**
- Canvas({"bg": "black", "grid": "3*2", aspect_ratio="16:9"})

**Scene**
- MovingCameraScene
- ZoomedScene

**Grid**
- 3*2
- Custom

**Animate**
- animate(reveal, smooth)
- animate(reveal, draw)
- animate

**Text**
- text.font('sans', '#ffffff')
- text.style({})
- text.animate(reveal, typewriter)

**Node**
- s1 = Scene(), s2 = Scene() #here node is connection, transition and timing between two or more scene, object and element
if s1 get's bigger how others scene adjust their position

**Object**
- geometric object (line, triangle, square, rectangle)
- graph
- image
- audio
- subtitle
- Icons
- UI Elements (progress bar, buttons, slider, timeline)


Inpired by manim library which is use for making math video so i want to make similar kind of video library to make the video from components like text, object, images, audio etc.
Every element can be animate. FFMPEG is the main library to render the video. It is node based with graphical structured design. Here every object treat as component. It should support complex animation and transition smoothly.

Position 
supported image file [png, jpg, jpeg, webp, gif]
quality at export {"ql": 720p, "qh": 1080p, "qk": 4k}

## Coding Structure and Quality
- Modular, scalable, pluggable
- Agent Friendly (Include SKills and LLM text)
- Developer Friendly Docs

## Example

text scene
txt1 = Scene.add_text('Hello world')
txt1.font('sans', '#fffff')
txt1.render(timing, position)