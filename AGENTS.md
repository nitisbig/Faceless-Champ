# Faceless Champ: guide for coding agents

Faceless Champ is a Python 3.12+ library for programmatic video, built for developers and AI agents.
There are three packages:

- `faceless_champ` (core, `src/`): scenes, components, themes, rendering, FFmpeg export. Core never imports kit.
- `facelesschamp_kit` (`facelesschamp-kit/`): blocks, shot templates, charts, diagrams, code, web and OS clips.
- `facelesschamp_agent` (`facelesschamp-agent/`): planning, audits and delivery around kit (`fc-agent`).

## Read in this order

1. [CHEATSHEET.md](CHEATSHEET.md): tested patterns. Start every scene from one of them.
2. [llms.txt](llms.txt): a compact map of the core API. Then [facelesschamp-kit/llms.txt](facelesschamp-kit/llms.txt) for kit.
3. [docs/api.md](docs/api.md): only the sections for the components you use.

Skip `docs/v2/`, `docs/audits/`, `docs/decisions/`, `output/`, `build/`, `scratch/` and `project-map/`.
They are history and generated files, not instructions.

## Rules for scenes

1. Activate a theme (`with Theme.named("midnight").use():`). No hard-coded colors, fonts or sizes.
2. All text uses `role=` (`display`, `title`, `heading`, `body`, `label`, `caption`). Wrap copy with `theme.fit(...)`.
3. Keep copy short. A `TextBudgetError` or `TEXT_BUDGET` means cut or split the copy. Never shrink it or disable budgets.
4. Lay out with `canvas.safe_area()` and `Bounds.columns/rows/grid/inset/fit`.
5. Use primitives instead of re-drawing them: `Stat`, `Pill`, `Badge`, `Callout`, `Arc`, `Dot`, `Divider`, `GlassCard`, `IconText`.
6. Animate with `scene.reveal(...)`, `scene.play(..., rate_func="emphasized")` and `obj.animate.through(...)`.
7. For a single standard beat, prefer `fc-kit shot <template> content.json` or the kit shot blocks.
8. End scripts with `run(build)`. Check `python scene.py --frame T` and `--audit` before `--preview` or a full render.

## Commands

```bash
python -m pip install -e . -e ./facelesschamp-kit -e ./facelesschamp-agent
python -m pytest tests facelesschamp-kit/tests facelesschamp-agent/tests
ruff check . && ruff format --check .
python scripts/sync_reference_docs.py         # after changing llms.txt, docs/*.md or public exports
python scripts/build_font_coverage.py         # after adding or replacing a bundled font
```

## Changing the library

- Keep the public API lazy: add exports to `_EXPORTS` and append them to the end of `__all__` in
  `src/faceless_champ/__init__.py`.
- New user-facing behaviour needs a test. Examples in `CHEATSHEET.md` are executed by `tests/test_agent_docs.py`.
- V1 pixel goldens (`tests/fixtures/minimal_scenes.py`) pin explicit fonts. Do not regenerate the hashes casually.
