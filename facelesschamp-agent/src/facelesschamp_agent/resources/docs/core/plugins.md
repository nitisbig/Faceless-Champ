# Plugins and function sources

Two ways to bring outside rendering into Faceless Champ:

- **`FunctionSource`** wraps any Python function that returns pixels. Use it for numpy
  shaders, matplotlib figures, simulation frames, or another engine's output.
- **Plugins** package themes, easings, components, sources, kit shot templates and
  agent-discoverable capabilities so other projects and agents can find them.

## FunctionSource

`FunctionSource(fn, size=(w, h), duration=None, fps=None, key=None, setup=None)` calls
`fn(t, size)` for each frame it needs. `t` is source time in seconds, starting when the
viewport enters the scene and clamped to `duration`. Return a PIL image or a numpy array
(`HxW`, `HxWx3` or `HxWx4`, either `uint8` or floats in 0-1), ideally at `size`; any
other size is resized. Place the source with `Viewport(source, ...)` or `source.viewport(...)`.

```python
import numpy as np

from faceless_champ import Scene, Theme, raster_source


@raster_source(size=(480, 270), duration=4, fps=30)
def plasma(t, size):
    w, h = size
    y, x = np.mgrid[0:h, 0:w] / max(w, h)
    v = np.sin(10 * x + t * 2) + np.sin(10 * y - t * 3) + np.sin(10 * (x + y) + t)
    v = (v + 3) / 6
    return np.dstack([v, 0.4 * v, 1 - v])


theme = Theme.named("neon")
with theme.use():
    scene = Scene(theme.canvas())
    box = scene.canvas.safe_area().aspect(16 / 9)
    scene.reveal(plasma.viewport(width=box.width, height=box.height, position=box.center))
    scene.wait(4)
```

- **`fps`** quantizes time, so identical frames are rendered once and cached. Leave it as
  `None` for continuous motion.
- **`key`** is part of the cache identity. Change it when the function reads outside data
  such as files or parameters. By default the identity comes from the function's code
  and closure values.
- **`setup(size)`** runs once per render session. The function then receives its result:
  `fn(t, size, state)`. If that state has a `close()` method, it is called when the
  session ends. Use it for expensive objects such as a matplotlib figure or a model.

```python
from faceless_champ import FunctionSource, Scene, Theme


def make_figure(size):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(size[0] / 100, size[1] / 100), dpi=100)
    fig.close = lambda: plt.close(fig)
    return fig


def sine_chart(t, size, fig):
    import numpy as np
    from PIL import Image

    fig.clear()
    ax = fig.add_subplot()
    xs = np.linspace(0, 6.28, 200)
    ax.plot(xs, np.sin(xs + t * 2), color="#2EE6FF", lw=3)
    ax.set_axis_off()
    fig.canvas.draw()
    return Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba())


theme = Theme.named("neon")
with theme.use():
    scene = Scene(theme.canvas())
    chart = FunctionSource(sine_chart, size=(800, 450), duration=3, fps=15, setup=make_figure)
    scene.add(chart.viewport(position=scene.canvas.bounds.center))
    scene.wait(3)
```

## Writing a plugin

```python
from faceless_champ import Capability, FunctionSource, Plugin, Theme
from faceless_champ.easing import cubic_bezier
from faceless_champ.theme import THEMES


def stripes(t, size):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", size, "#101522")
    draw = ImageDraw.Draw(image)
    for x in range(-size[1], size[0], 40):
        offset = int(t * 80) % 40
        draw.line((x + offset, 0, x + offset + size[1], size[1]), fill="#2EE6FF", width=8)
    return image


plugin = Plugin(
    name="studio-extras",
    version="1.0",
    summary="House theme, easing and an animated stripes source",
    themes={"studio": Theme("studio", THEMES["midnight"].colors, radius=12)},
    easings={"studio-swift": cubic_bezier(0.3, 0.0, 0.0, 1.0)},
    sources={"stripes": lambda **options: FunctionSource(stripes, **options)},
    capabilities=(
        Capability(
            "stripes", "Animated diagonal stripe backdrop", "faceless_champ.plugins.source", tags=("background",)
        ),
    ),
)
```

Publish it from your package's `pyproject.toml`:

```toml
[project.entry-points."faceless_champ.plugins"]
studio-extras = "studio_extras:plugin"       # a Plugin, or a zero-argument function returning one
```

For a project-local plugin that isn't packaged, set
`FACELESS_CHAMP_PLUGINS="my_project.fc_plugin:plugin"`. You can also call
`faceless_champ.plugins.register(plugin)` at runtime.

Once loaded:

- `Theme.named("studio")` and `rate_func="studio-swift"` work.
- `faceless_champ.plugins.source("stripes", size=(640, 360), duration=5)` builds the source.
- `faceless_champ.plugins.component(name)` returns a component.
- Kit shot templates appear in `fc-kit shot --list`.
- Every contribution is listed by `fc-agent capabilities` and
  `python -m faceless_champ plugins`.

## Rules

- **Built-ins always win.** A plugin cannot replace a built-in theme or easing. Names may not
  clash with another plugin's, and names cannot contain `:`.
- **Failures are reported, not fatal.** A plugin that fails to load is listed with its error
  by `plugin_report()`, `fc-kit doctor` and `python -m faceless_champ plugins`. Rendering
  continues without it.
- **Discovery is lazy and runs once.** It happens on the first lookup that misses a built-in
  name, or when you list plugins. Loading a plugin runs its code, so only install plugins
  you trust.
- **Shot templates** are kit blocks: frozen dataclasses whose
  `compose(ctx, bounds) -> BlockBuild` returns fresh components. Their fields become the
  JSON content keys for `fc-kit shot`.
