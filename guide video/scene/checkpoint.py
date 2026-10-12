"""Executed only by explicit playground preparation, never by video playback."""

from hello import Hello

from faceless_champ import Circle, Text
from faceless_champ.playground.runtime import emit

scene = Hello().build()
objects = []
for entry in scene.entries:
    component = entry.component
    if isinstance(component, Text):
        kind = "text"
        props = {"text": component.text, "font_size": component.font_size, "color": component.color}
    elif isinstance(component, Circle):
        kind = "circle"
        props = {"radius": component.width / 2, "fill": component.fill, "stroke": component.stroke}
    else:
        raise TypeError(f"Unsupported example component: {type(component).__name__}")
    props["position"] = component.position
    objects.append(
        {
            "kind": kind,
            "props": props,
            "start": entry.start,
            "end": entry.end,
            "initial": entry.initial,
            "tracks": [
                {
                    "property": t.property,
                    "start": t.start,
                    "duration": t.duration,
                    "initial": t.initial,
                    "target": t.target,
                    "easing": t.easing.__name__,
                }
                for t in entry.tracks
            ],
        }
    )
emit(
    "scene",
    {
        "canvas": {"width": scene.canvas.width, "height": scene.canvas.height, "bg": scene.canvas.bg},
        "duration": scene.duration,
        "objects": objects,
    },
)
print(f"Hello · {len(objects)} components")
if objects:
    print(f"1920 × 1080 · {scene.duration:g}s")
