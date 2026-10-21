# Faceless Champ project atlas

Open [index.html](index.html) directly in a browser. The generated page contains
its own data, scripts, styles, diagrams and bundled DM Sans font; no installation,
network connection or web server is needed. Source/documentation links point back
into this checkout. Keep the atlas in `project-map/` for those links to work.

The seven views cover the ecosystem, architecture, feature catalog, motion
studies, premium scene drafts, Git milestones and repository/package structure.
Search with Ctrl/Cmd+K, open feature details, filter projects/capabilities, scrub
motion studies, and print the current view. Mobile navigation is available from
the top-left menu.

From the repository root, refresh the snapshot with:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/sync_reference_docs.py
python3 project-map/build.py
python3 project-map/build.py --check
```

The builder uses the standard library. It reads the shared V2 capability metadata
from `docs/v2/public-capabilities.json`, checks versions/dependencies against package
manifests, and uses Python ASTs for the current Kit web/desktop APIs. It also
enumerates premium-reference READMEs, captures local Git history and samples the
standalone Spring kernel. It does not execute authored scenes, prepare code/web
assets, render video, run tests, or contact external services.

`--check` returns a nonzero status for a stale snapshot and never writes the page.
Refresh references first when changing public APIs or manifests. Current feature
cards follow V2 ownership; the timeline preserves labeled V1 history, including
the later removal of ChessChamp. Test-module counts include nested domain tests.
The existing package paths and disposable-cache policy are explained in the
[repository layout guide](../docs/v2/repository-layout.md).

`src/catalog.js` owns curated feature descriptions, project summaries and major
milestones. `src/app.js` owns navigation and interactions; `src/style.css` and
`src/page.html` own the presentation. The builder bundles these into `index.html`.
Review curated material when the underlying capabilities change. Automatic counts
describe the current source; recorded verification figures describe their linked
reports and are not new test results. Gallery diagrams are explanatory schematics,
not video frames; authored duration does not establish full-export verification.

To inspect through HTTP, serve the repository root so source links remain valid:

```bash
python3 -m http.server 8766 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8766/project-map/>.

Previous demo data and media evidence were retired. The current Hello World opening
is structurally checked only; rendering and visual approval remain pending.
