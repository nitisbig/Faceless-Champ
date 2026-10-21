# V2 checkout layout and cleanup

The three independently installed Python packages retain their existing checkout
paths. V2 changed ownership and implementation inside them; a new enclosing
`core/kit/agent` folder hierarchy is not required.

```text
Faceless Champ/
├── pyproject.toml                 Core manifest
├── src/faceless_champ/            Core primitives, time, rendering and export
│   ├── _rendering/                Shared compilation, evaluation and resources
│   ├── backends/                  Pillow, optional Skia and ModernGL
│   ├── integrations/              Optional PyVista, build123d and Trimesh
│   └── assets/                    Installed Core fonts, icons and sound effects
├── facelesschamp-kit/             Independent Kit manifest, docs and tests
│   └── src/facelesschamp_kit/
│       ├── charts/ maps/ coding/ diagrams/ desktop/
│       ├── playground/ web/ engineering/
│       └── compiler.py rendering.py project.py
├── facelesschamp-agent/           Independent Agent manifest, docs and tests
│   └── src/facelesschamp_agent/    Planning, discovery, evidence and review policy
├── docs/v2/                      Architecture, migration and implementation records
├── website/                      Generated developer guides and their sources
├── project-map/                  Current offline atlas and its builder
├── scripts/ tests/               Repository tooling and focused Core checks
├── examples/ templates/          Runnable references and starter guidance
├── assets/ skills/ agents/       Authoring references and instructions
├── my-project/                  Existing user project work
├── output/                      Render artifacts and validation evidence
└── design inspiration/          Supplied design material
```

Root `assets/` and packaged `src/faceless_champ/assets/` have different uses.
The former contains authoring/reference material; the latter is distributed with
Core. Kit owns its map/flag, diagram and sample assets. No asset copies were
deleted merely because their parent directories have similar names.

Old Core domain names such as `charts.py`, `flow.py`, `web.py` and `chess.py`
remain small migration notices. They do not contain the former domain engines
and do not import Kit upward. `arch/__init__.py` retains supported Core-local
geometry aliases. Keep these intentional compatibility/migration entrypoints;
see [M4 migration](m4-migration.md).

## Disposable generated files

The cleanup helper lists untracked `__pycache__`, `.pytest_cache`, `.ruff_cache`
directories within maintained source/tool/test roots, plus root/Kit/Agent build
directories. It skips tracked content and directory symlinks. It does not traverse
user projects, environments, output/evidence or design material. Package metadata
and explicit prepared-asset caches are retained.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/clean_dev_caches.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/clean_dev_caches.py --apply
```

Python and test tools can recreate these caches during ordinary use. Their presence
does not indicate that the V1 implementation is running.

## Current guides and atlas

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/sync_reference_docs.py
python3 project-map/build.py
python3 project-map/build.py --check
```

The atlas reads shared V2 metadata and the actual Kit web/desktop paths. Curated
current features and repository rows describe V2; the dated historical timeline
retains the V1 chess introduction and explains its later removal. The generated
HTML works offline. Read-only drift checking catches outdated snapshots.

This follow-up corrects the missed atlas synchronization from the initial M5
implementation. It changes repository tooling/documentation and removes generated
caches; it does not rename installed packages, move user projects or certify
additional runtime/platform/render coverage.
