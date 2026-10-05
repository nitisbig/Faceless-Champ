# Offline maps

Install with `pip install 'faceless-champ[maps]'` or use `uv run --extra maps`.
NumPy is loaded only when rendering maps; ordinary imports and other components do not require it.
All map data ships inside the wheel. Rendering never downloads files or needs an API key.

```python
from faceless_champ import Canvas, EarthMap, OutlineMap, SatelliteMap, Scene

scene = Scene(Canvas(1280, 720))
earth = EarthMap(width=650, height=650, position=(640, 360), longitude=20, latitude=15)
scene.add(earth)
scene.play(earth.animate.rotate(longitude=360), run_time=4)
scene.play(earth.animate.zoom_to("Nepal"), run_time=2)
scene.play(earth.animate.zoom_to("Pacific Ocean", zoom=1.3), run_time=2)
scene.render("earth.mp4", width=1280, height=720, fps=24)
```

## Components and animation

- `OutlineMap(country=None, fill=None, border_color="white", border_width=1, **kwargs)`
  draws the world, or fits an isolated country when a name/code is supplied. Islands and
  polygon holes are preserved. Width/height default to 800×400.
- `SatelliteMap(**kwargs)` uses a flat equirectangular map, default 800×400.
- `EarthMap(**kwargs)` projects the texture onto a shaded sphere, default 600×600.
  The area outside the sphere is transparent. Lighting is fixed relative to the viewer.
- Shared kwargs: `width`, `height`, `longitude=0`, `latitude=0`, `zoom=1`, and ordinary
  component transforms (`position`, `anchor`, `scale`, `rotation`, `opacity`, `z_index`).
  Angles are degrees, east/north positive. Latitude stays within −90…90; longitude wraps.
- `zoom_to(target, *, zoom=None)` sets center and magnification. `animate.zoom_to(...)`
  interpolates the same properties through `Scene.play`. Targets are case-insensitive
  country names, bundled ISO codes, or any of the five ocean names below. Automatic
  framing includes all bundled country polygons, including distant islands. An explicit
  positive zoom overrides automatic framing; zoom=1 restores baseline magnification.
- `rotate(degrees)` / `animate.rotate(degrees)` rotate flat-map content clockwise inside
  the fixed viewport. Earth uses `rotate(longitude=..., latitude=...)` with degree offsets.
  Direct setters return the component; animation methods return a chainable builder.
  Use separate play calls for globe rotation and named-target zoom. Flat rotation can be
  combined with zoom in one builder. `animate.rotate_to()` remains the ordinary whole
  component transform, independent of geographic rotation.
- Animated offsets use the current timeline state. Full longitude turns are preserved;
  named-target zoom takes the shortest longitude route. Latitude offsets must end within
  −90…90. Author direct setters before adding the component to a scene, as with other components.

Flat maps preserve a constant longitude/latitude scale and wrap horizontally, with transparency
beyond the poles. Earth uses an orthographic projection: zoom enlarges the surface within
its fixed viewport, so a close-up no longer shows the entire globe. Borders are low-resolution
1:110m geometry. The 4096×2048 January 2004 satellite composite has limited close-up detail;
it is not live imagery or elevation terrain. There are no automatic text labels.

Ocean framing presets (longitude, latitude, longitude span, latitude span):

| Target | Preset in degrees |
| --- | --- |
| Pacific Ocean | −160, 0, 140, 120 |
| Atlantic Ocean | −30, 0, 80, 140 |
| Indian Ocean | 80, −25, 90, 90 |
| Arctic Ocean | 0, 90, 360, 35 |
| Southern Ocean | 0, −75, 360, 30 |

These are camera presets, not legal or exact ocean boundaries. Unknown targets raise a
`ValueError` pointing to `supported_countries()`; countries missing from the source geometry
are not silently replaced with points.

## Showcase and checks

```bash
uv run --extra maps python examples/maps/render.py --preview
uv run --extra maps python examples/maps/render.py --quality hd --fps 30 --stills
uv run --extra maps python examples/maps/render.py --quality full-hd --fps 30 --overwrite
uv run --extra maps pytest tests/test_maps.py
```

Outputs default to `media/maps`; `--output` selects another directory. The 18-second
showcase covers world and Nepal outlines, satellite country/ocean zoom and rotation,
and a full globe spin followed by country and ocean zooms. Export uses existing render progress.
Projection uses 64-row strips and one cached decoded texture; output buffers depend on viewport
size, never a zoom-enlarged global raster. Ordinary bounded scene-frame caching handles holds.

## Sources and reproducible asset preparation

Country geometry: Natural Earth v5.1.2, 1:110m Admin 0 countries, obtained from the project's
[versioned GeoJSON](https://github.com/nvkelso/natural-earth-vector/blob/v5.1.2/geojson/ne_110m_admin_0_countries.geojson).
Natural Earth data is [public domain](https://www.naturalearthdata.com/about/terms-of-use/).
Its default de facto boundaries and low-resolution coverage are retained.

Texture: NASA Earth Observatory, [Blue Marble Next Generation, January base map](https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-map/),
NASA Visible Earth / Reto Stöckli. The 5400×2700 JPEG is resized with Pillow LANCZOS to
4096×2048 and saved as optimized quality-88 JPEG. Credit NASA Earth Observatory for the imagery;
no NASA insignia or endorsement is included.

To reproduce (Pillow 12.3.0 used for this build):

```bash
curl -L --fail --max-filesize 10000000 -o /tmp/ne-countries.json \
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_countries.geojson
curl -L --fail --max-filesize 10000000 -o /tmp/blue-marble.jpg \
  https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/bmng-base/january/world.200401.3x5400x2700.jpg
uv run python scripts/prepare_maps.py /tmp/ne-countries.json /tmp/blue-marble.jpg
```

The script drops unused properties, rounds coordinates to five decimals, preserves polygon
rings, and records SHA-256 source and output hashes in `assets/maps/manifest.json`. Each source
is capped at 10 MB; packaged map assets are capped at 5 MB. JPEG bytes may vary with encoder
version. The asset license file ships inside the wheel.

## Supported countries

`from faceless_champ import supported_countries` returns the current bundled names.
The following 177 entries reflect source coverage, not a claim of exhaustive sovereign-state coverage:

- Afghanistan
- Albania
- Algeria
- Angola
- Antarctica
- Argentina
- Armenia
- Australia
- Austria
- Azerbaijan
- Bangladesh
- Belarus
- Belgium
- Belize
- Benin
- Bhutan
- Bolivia
- Bosnia and Herzegovina
- Botswana
- Brazil
- Brunei
- Bulgaria
- Burkina Faso
- Burundi
- Cambodia
- Cameroon
- Canada
- Central African Republic
- Chad
- Chile
- China
- Colombia
- Costa Rica
- Croatia
- Cuba
- Cyprus
- Czechia
- Democratic Republic of the Congo
- Denmark
- Djibouti
- Dominican Republic
- East Timor
- Ecuador
- Egypt
- El Salvador
- Equatorial Guinea
- Eritrea
- Estonia
- Ethiopia
- Falkland Islands
- Fiji
- Finland
- France
- French Southern and Antarctic Lands
- Gabon
- Gambia
- Georgia
- Germany
- Ghana
- Greece
- Greenland
- Guatemala
- Guinea
- Guinea-Bissau
- Guyana
- Haiti
- Honduras
- Hungary
- Iceland
- India
- Indonesia
- Iran
- Iraq
- Ireland
- Israel
- Italy
- Ivory Coast
- Jamaica
- Japan
- Jordan
- Kazakhstan
- Kenya
- Kosovo
- Kuwait
- Kyrgyzstan
- Laos
- Latvia
- Lebanon
- Lesotho
- Liberia
- Libya
- Lithuania
- Luxembourg
- Madagascar
- Malawi
- Malaysia
- Mali
- Mauritania
- Mexico
- Moldova
- Mongolia
- Montenegro
- Morocco
- Mozambique
- Myanmar
- Namibia
- Nepal
- Netherlands
- New Caledonia
- New Zealand
- Nicaragua
- Niger
- Nigeria
- North Korea
- North Macedonia
- Northern Cyprus
- Norway
- Oman
- Pakistan
- Palestine
- Panama
- Papua New Guinea
- Paraguay
- Peru
- Philippines
- Poland
- Portugal
- Puerto Rico
- Qatar
- Republic of Serbia
- Republic of the Congo
- Romania
- Russia
- Rwanda
- Saudi Arabia
- Senegal
- Sierra Leone
- Slovakia
- Slovenia
- Solomon Islands
- Somalia
- Somaliland
- South Africa
- South Korea
- South Sudan
- Spain
- Sri Lanka
- Sudan
- Suriname
- Sweden
- Switzerland
- Syria
- Taiwan
- Tajikistan
- Thailand
- The Bahamas
- Togo
- Trinidad and Tobago
- Tunisia
- Turkey
- Turkmenistan
- Uganda
- Ukraine
- United Arab Emirates
- United Kingdom
- United Republic of Tanzania
- United States of America
- Uruguay
- Uzbekistan
- Vanuatu
- Venezuela
- Vietnam
- Western Sahara
- Yemen
- Zambia
- Zimbabwe
- eSwatini
