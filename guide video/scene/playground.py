"""Project composition: prepared Python scenes replayed with native core primitives."""

from bisect import bisect_right

from faceless_champ import Animation, Canvas, Circle, PillowRenderer, PlaygroundCanvas, Scene, Text
from faceless_champ.animation import linear, smooth


def tuple_value(value):
    return tuple(value) if isinstance(value, list) else value


def replay(record, only=()):
    scene = Scene(Canvas(**record["canvas"]))
    for item in record["objects"]:
        if only and item["kind"] not in only:
            continue
        props = dict(item["props"])
        props["position"] = tuple(props["position"])
        component = (Text if item["kind"] == "text" else Circle)(**props)
        for key, value in item["initial"].items():
            if hasattr(component, key):
                setattr(component, key, tuple_value(value))
        with scene.at(item["start"]):
            scene.add(component)
        for motion in sorted(item["tracks"], key=lambda t: t["start"]):
            key = motion["property"]
            with scene.at(motion["start"]):
                scene.play(
                    Animation(component, {key: tuple_value(motion["target"])}, {key: tuple_value(motion["initial"])}),
                    run_time=motion["duration"],
                    rate_func={"smooth": smooth, "linear": linear}[motion["easing"]],
                )
        if item["end"] is not None:
            with scene.at(item["end"]):
                scene.remove(component)
    scene.wait_until(record["duration"])
    return scene


class ExamplePlayback(PlaygroundCanvas):
    """A lesson-specific result viewport; reads only immutable prepared scene data.

    Native Text/Circle scenes are rasterized at the requested export scale rather
    than upscaling preview screenshots. Keys map lesson age to example seconds.
    """

    def __init__(self, prepared, *, checkpoint=-1, keys=((0, 2),), only=(), **kwargs):
        self.keys = tuple(keys)
        self.checkpoint = checkpoint
        self.only = tuple(only)
        self._replays = {}
        self._renderer = PillowRenderer(1, frame_cache_mb=8, code_cache_mb=0)
        super().__init__(prepared, **kwargs)

    def selection(self, age):
        if self.checkpoint is not None:
            return self.checkpoint % len(self._results)
        time = self.source_start + age
        return next((i for i in reversed(range(len(self._results))) if time >= self.script.checkpoints[i].publish), 0)

    def sample_time(self, age):
        i = max(0, bisect_right([k[0] for k in self.keys], age) - 1)
        a, value = self.keys[i]
        if i + 1 < len(self.keys):
            b, target = self.keys[i + 1]
            return value + (target - value) * max(0, min(1, (age - a) / (b - a)))
        return value

    def frame_key(self, age):
        return self.selection(age), round(self.sample_time(age), 9)

    def frame_image(self, age, factor=1):
        index = self.selection(age)
        if index not in self._replays:
            self._replays[index] = replay(self._results[index]["values"]["scene"], self.only)
        scene = self._replays[index]
        return self._renderer.frame(
            scene,
            min(scene.duration, max(0, self.sample_time(age))),
            (max(1, round(self.width * factor)), max(1, round(self.height * factor))),
        )
