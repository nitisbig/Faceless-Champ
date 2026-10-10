"""Antialias the film's individual vector layers rather than its empty black canvas.

Faceless Champ still typesets/rasterizes every primitive. Small cached supersampled
layers make the 1080p film practical on this machine without reducing antialiasing.
Unsupported masks or nonuniform transforms use the standard renderer.
"""

from collections import OrderedDict

from PIL import Image

from faceless_champ import Group, PillowRenderer, Scene
from faceless_champ.layout import transform_point


class FilmRenderer(PillowRenderer):
    def __init__(self, antialias=2):
        super().__init__(antialias, frame_cache_mb=24, caption_cache_mb=0)
        self.layers = OrderedDict()
        self.layer_bytes = 0
        self.last_signature = None
        self.last_frame = None

    def frame(self, node, time, size):
        if not isinstance(node, Scene):
            return super().frame(node, time, size)
        node.build()
        visible = []
        unsupported = False

        def collect(entries, parents=()):
            nonlocal unsupported
            for entry in sorted(entries, key=lambda e: e.component.z_index):
                if time < entry.start or (entry.end is not None and time >= entry.end):
                    continue
                state = entry.state_at(time)
                if state["opacity"] <= 0:
                    continue
                if (
                    entry.component.mask is not None
                    or entry.component.anchor != "center"
                    or state["clip"] != (0, 0, 1, 1)
                    or state["scale_x"] != 1
                    or state["scale_y"] != 1
                ):
                    unsupported = True
                if isinstance(entry.component, Group):
                    collect(entry.children, ((entry.component._origin, state),) + parents)
                else:
                    visible.append((entry.component, state, max(0, time - entry.start), parents))

        collect([e for e in node.entries if e.parent is None])
        if unsupported:
            return super().frame(node, time, size)
        signature = (
            node,
            size,
            tuple(
                (c, tuple(s.items()), tuple((o, tuple(p.items())) for o, p in parents))
                for c, s, age, parents in visible
            ),
        )
        if signature == self.last_signature:
            return self.last_frame.copy()
        ratio = min(size[0] / node.canvas.width, size[1] / node.canvas.height)
        factor = ratio * self.antialias
        frame = Image.new("RGBA", size, node.canvas.bg)
        for c, state, age, parents in visible:
            x, y = state["position"]
            scale, rotation, opacity = state["scale"], state["rotation"], state["opacity"]
            for origin, parent in parents:
                x, y = transform_point((x, y), origin, parent)
                scale *= parent["scale"]
                rotation += parent["rotation"]
                opacity *= parent["opacity"]
            # Position and opacity do not change the underlying antialiased shape.
            key = (
                c,
                factor,
                scale,
                rotation,
                tuple((k, v) for k, v in state.items() if k not in {"position", "opacity", "rotation", "scale"}),
            )
            sprite = self.layers.get(key)
            if sprite is None:
                sprite = self._sprite(c, state, factor, age)
                if scale != 1:
                    sprite = sprite.resize(
                        (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale))),
                        Image.Resampling.LANCZOS,
                    )
                if rotation:
                    sprite = sprite.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)
                if self.antialias > 1:
                    sprite = sprite.resize(
                        (max(1, round(sprite.width / self.antialias)), max(1, round(sprite.height / self.antialias))),
                        Image.Resampling.LANCZOS,
                    )
                cost = sprite.width * sprite.height * 4
                if cost <= 48 * 1024 * 1024:
                    while self.layers and self.layer_bytes + cost > 48 * 1024 * 1024:
                        _, old = self.layers.popitem(last=False)
                        self.layer_bytes -= old.width * old.height * 4
                    self.layers[key] = sprite
                    self.layer_bytes += cost
            else:
                self.layers.move_to_end(key)
            if opacity < 1:
                sprite = sprite.copy()
                sprite.putalpha(sprite.getchannel("A").point(lambda a, p=opacity: round(a * p)))
            frame.alpha_composite(sprite, (round(x * ratio - sprite.width / 2), round(y * ratio - sprite.height / 2)))
        self.last_signature, self.last_frame = signature, frame.copy()
        return frame
