"""Finite, nested animation schedules compiled transactionally."""

from copy import copy, deepcopy

from .animation import Animation, _cycles
from .components import finite


class Schedule:
    def __init__(self, *children, duration=1, delay=0):
        if not children or any(not isinstance(c, (Animation, Schedule)) for c in children):
            raise TypeError("Schedules require animations or schedules")
        self.children = children
        self.duration = finite(duration, "duration", 0.000001)
        self.delay = finite(delay, "delay", 0)

    def child_time(self, child):
        return child.run_time if isinstance(child, Schedule) else self.duration


class Stagger(Schedule):
    def __init__(self, *children, lag=0.1, duration=1, delay=0):
        super().__init__(*children, duration=duration, delay=delay)
        self.lag = finite(lag, "lag", 0)

    @property
    def run_time(self):
        return self.delay + max(i * self.lag + self.child_time(c) for i, c in enumerate(self.children))


class Succession(Schedule):
    @property
    def run_time(self):
        return self.delay + sum(self.child_time(c) for c in self.children)


class Repeat(Schedule):
    def __init__(self, child, *, cycles, ping_pong=False, duration=1, delay=0):
        super().__init__(child, duration=duration, delay=delay)
        self.cycles = _cycles(cycles)
        if not isinstance(ping_pong, bool):
            raise TypeError("ping_pong must be bool")
        self.ping_pong = ping_pong

    @property
    def run_time(self):
        return self.delay + self.child_time(self.children[0]) * self.cycles


def play_schedule(scene, animations, run_time, rate_func):
    # Copy entries, preserving the public authoring objects as ownership keys.
    trial = copy(scene)
    trial.entries = deepcopy(scene.entries)
    mapping = {id(old): new for old, new in zip(scene.entries, trial.entries)}
    trial._objects = {c: mapping[id(e)] for c, e in scene._objects.items()}
    root = Stagger(*animations, lag=0)
    natural = root.run_time
    factor = 1 if run_time is None else finite(run_time, "run_time", 0.000001) / natural
    start = scene.time

    def flatten(node, offset, duration=1):
        if isinstance(node, Animation):
            return [{"at": offset, "duration": duration * factor, "animation": node}]
        offset += node.delay * factor
        if isinstance(node, Repeat):
            span = node.child_time(node.children[0]) * factor
            original = flatten(node.children[0], offset, node.duration)
            events = list(original)
            for cycle in range(1, node.cycles):
                reverse = node.ping_pong and cycle % 2
                for event in original:
                    local = event["at"] - offset
                    at = offset + cycle * span + (span - local - event["duration"] if reverse else local)
                    events.append({"at": at, "duration": event["duration"], "reference": event, "reverse": reverse})
            return events
        events = []
        cursor = offset
        for i, child in enumerate(node.children):
            at = offset + i * node.lag * factor if isinstance(node, Stagger) else cursor
            events.extend(flatten(child, at, node.duration))
            cursor += node.child_time(child) * factor
        return events

    for event in sorted(flatten(root, start), key=lambda e: e["at"]):
        trial._cursor = event["at"]
        if "animation" in event:
            batch = [event["animation"]]
        else:
            batch = []
            for c, t in event["reference"]["tracks"]:
                reverse = event["reverse"]
                initial, target = (t.target, t.initial) if reverse else (t.initial, t.target)
                frames = t.keyframes
                if reverse and frames:
                    frames = tuple((1 - p, v) for p, v in reversed(frames))
                easing = (lambda x, f=t.easing: 1 - f(1 - x)) if reverse else t.easing
                batch.append(
                    Animation(
                        c,
                        {t.property: target},
                        {t.property: initial},
                        {t.property: frames} if frames else None,
                        rate_func=easing,
                    )
                )
        before = {c: len(e.tracks) for c, e in trial._objects.items()}
        trial._play(*batch, run_time=event["duration"], rate_func=rate_func if "animation" in event else None)
        event["tracks"] = [(c, t) for c, e in trial._objects.items() for t in e.tracks[before.get(c, 0) :]]

    # Keep existing Entry references valid for callers inspecting the timeline.
    for old, new in zip(scene.entries, trial.entries):
        old.tracks = new.tracks
    old_by_trial = {id(new): old for old, new in zip(scene.entries, trial.entries)}
    for new in trial.entries[len(scene.entries) :]:
        new.parent = old_by_trial.get(id(new.parent), new.parent)
        scene.entries.append(new)
    scene._objects = {c: old_by_trial.get(id(e), e) for c, e in trial._objects.items()}
    scene._cursor = start + natural * factor
    return scene
