# Approved tutorial templates

Each design has its own folder. Templates contain reusable style and component
helpers; lesson content, narration and cue timing stay in the authored project.

| Template | Reusable source | Editable defaults |
| --- | --- | --- |
| Coding tutorial | [Kit design pack](../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/TEMPLATE.md) | [style.json](../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.json) |

fc-agent selects `coding-tutorial` only for landscape coding tutorials without
custom design or instructions. Custom project design and explicit instructions
take priority. Selection creates a project-owned `templates/coding-tutorial/`
folder and never overwrites its edits. An untouched generated starter design is
recognized as a default, not as custom direction.

For the current reference, edit its [local style](../examples/programming/hello_world/templates/coding-tutorial/style.json).
For future projects, edit that project's `templates/coding-tutorial/style.json`.
Use `background`, `accent`, editor colors, `code_size`, `terminal_size`, insets,
window scale and spring tuning. Re-run layout checks after geometry changes.

Generated render.py supports `--fps` and `--quality low|high|4k`. Quality selects
720p, 1080p or 2160p independently of preview/full length. Omitted options retain
project export profiles; explicit options leave those profiles unchanged.
