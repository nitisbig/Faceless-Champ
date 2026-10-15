# FacelessChamp — Networking Explained UI Pack

A consistent neon-gradient visual kit for educational networking, Internet, system-design, and cloud architecture videos.

## Contents
- `svg/nodes/` — labeled dark glass cards AND transparent `_icon` variants.
- `svg/connections/` — straight, curved, wave, dashed, request/response, branch, fiber, secure, ping, and animated-packet *visuals*.
- `svg/protocols/` — 19 reusable network protocol and OSI layer tags.
- `svg/topologies/` — point-to-point, bus, star, ring, mesh, tree layouts.
- `svg/panels/` — Packet Inspector, Connection Status, HTTP Request, TCP handshake.
- `png/` — 2× raster renders with alpha transparency corresponding to each SVG.
- `previews/` — contact sheet and visual style reference.
- `manifest.json` — item names, paths, and intended use.

## Video use
SVGs are infinitely scalable, preferable for Python-generated 1080p/4K video. The PNGs are transparency-enabled for direct use as overlays.

**Python (Manim):**
```python
from manim import *
class Network(Scene):
    def construct(self):
        client = SVGMobject('svg/nodes/laptop_icon.svg').scale(0.85)
        server = SVGMobject('svg/nodes/server_icon.svg').scale(0.85)
        client.shift(LEFT * 3.5)
        server.shift(RIGHT * 3.5)
        self.play(FadeIn(client), FadeIn(server))
        self.play(Create(Line(client.get_right(), server.get_left(), color=BLUE)))
```

**Python (Pillow / custom renderer):** load a `png/` asset as RGBA and alpha composite it over a video frame.

**Python (SVG to PNG):**
```python
import cairosvg
cairosvg.svg2png(url='svg/connections/straight_gradient.svg', write_to='connection.png', output_width=2000)
```

## Animation ideas
1. Animate source and destination nodes entering with slight scale + opacity easing.
2. Draw the connector left-to-right (path trim/mask or a crop reveal).
3. Animate a small packet along the connector to illustrate an IP hop.
4. Change protocol tags during DNS → TCP/TLS → HTTP explanation.
5. Shift from point-to-point → star → mesh during network-topology scenes.

The displayed IP addresses, latency, throughput, packet loss, and HTTP values are *illustrative sample data*, not live network readings.

## Palette
- Base background: #07111F (or #081427)
- Electric cyan: #36E5FA
- Network blue: #458EFF
- Violet: #A679FF
- Pink: #F575E2
- Secure green: #39EAC4
- Alert red: #FC718E
- Warm packet amber: #FFBE69

Recommended video typography: Inter, DejaVu Sans, or Manrope. Keep 6–8% margins in 16:9 video frames and limit glow to highlighted connections.

All SVGs are editable and have no external font/image dependencies. Produced for FacelessChamp.
