# OS UI rendering

`faceless_champ.os_ui` renders authored macOS-style tutorials offline with Pillow.
It is a simulated desktop: files, Wi-Fi, volume, and other settings belong to the video.
No host desktop, browser, network connection, or macOS installation is needed.

## First scene

```python
from faceless_champ import Scene
from faceless_champ.os_ui import File, Folder, OSClip, OSScript, VirtualFileSystem

files = VirtualFileSystem(Folder("home", "Home", (
    Folder("docs", "Documents", (
        File("notes", "Notes.txt", "A simple idea, clearly explained."),
        Folder("archive", "Archive"),
    )),
)))
script = (OSScript().open_folder("docs")
          .rename("notes", "Launch Notes.txt")
          .drag("notes", "archive")
          .open_settings("appearance")
          .set_value("appearance:theme", "dark")
          .wait(1))
scene = Scene()
scene.add(OSClip(files, script, position=(960, 540)))
scene.wait(script.duration)
```

Save as `tutorial.py`, then run:

```bash
faceless-champ render tutorial.py scene -o output/tutorial.mp4
```

## Virtual files

`VirtualFileSystem(Folder(...))` validates unique IDs and sibling names. Define nested
`Folder(id, name, children)` and `File(id, name, text="", image=None)` records.
IDs survive rename/move. `image` accepts a supplied local image file; assets are loaded
when `OSClip` compiles, so missing images fail before export. Text previews preserve
line breaks and show the lines that fit the preview window.

Filesystem methods are `children`, `node`, `visible`, `create_folder`, `rename`, `copy`,
`move`, `trash`, and `restore`. They modify only the virtual model. The clip snapshots
its inputs, so later changes to the source tree or script do not change the video.
Copy takes `new_id`; descendants receive `new_id/original_id`. Restoring to a folder
with a conflicting name or a trashed parent raises an error.

## Actions and timing

Every action accepts `at`, `duration` (default one second), and `cursor` (default true).
Omit `at` to append after the previous action. Explicit times must be chronological
and non-overlapping, including cursor actions. `wait(seconds)` adds a hold.

| Action | Purpose |
| --- | --- |
| `open_folder(id)`, `back()`, `forward()`, `up()` | Navigate folders and history |
| `select(id)`, `set_view("list")`, `search(text)` | Select, change icon/list view, filter current folder |
| `scroll(rows, window="finder")` | Scroll by rows, clamped to available content |
| `create_folder(id, name)`, `rename(id, name)` | Create or rename with typing feedback |
| `copy(id, destination, new_id, name=None)` | Copy a virtual subtree |
| `move(id, destination)`, `drag(id, destination)` | Move with a dragged icon; destination must be visible |
| `trash(id, confirm=True)`, `confirm(accept=True)` | Show and answer a confirmation dialog |
| `open_trash()`, `restore(id)` | View Trash and restore an item |
| `preview(id)` | Show authored text or a supplied image |
| `open_settings(page)`, `set_value("page:control", value)` | Change simulated settings |
| `window(id, action, ...)` | Open, close, focus, minimize, restore, maximize, move, resize |
| `move_cursor(target)` or `move_cursor(position=(x, y))` | Explicit cursor movement |
| `click(target)`, `double_click(target)`, `right_click(target)` | Interact with visible controls/files |
| `type_text(target, text)`, `menu("File")` | Type into a text field or open the starter File menu |

Window IDs are `finder`, `settings`, and `preview`. Move uses `position=(x, y)`;
resize uses `size=(width, height)`. Maximize toggles; restore also reverses maximization.
The preview needs a file selected through `preview(id)` before it has content.

Normal semantic actions move the cursor during the first 35% of their interval.
Interaction feedback follows, the logical change commits at 60%, and transitions
settle by 90%. Dragging moves the icon to its destination before the commit. Cursor-free
actions suppress choreography. Targets must be visible even with cursor choreography disabled. Reopening an isolated
window without a dock uses `window("finder", "open", cursor=False)`.
Use sequential scripts for one cursor; do not schedule concurrent OS actions.

`state_at(time)` returns an independent logical snapshot. `bounds_for(target, time)`
returns visible bounds in **viewport-local design pixels at original script time**,
including window geometry transitions. Named targets include `file:ID`, `sidebar:ID`,
`finder:back`, `finder:search`, `finder:trash`, `finder:title`, `dock:settings`,
`page:appearance`, `control:sound:volume`, `menu:open`, and `dialog:confirm`.
Bare file IDs also resolve. Occluded, scrolled-off, and missing targets raise errors;
navigate, scroll, or focus the window before interacting.

## Settings and visual customization

`MacOSPreset` accepts `appearance="light"` or `"dark"`, `wallpaper` (a color),
`accent`, `font`, `font_size` (10–32, default 22), `clock`, `cursor_color`, `cursor_size`, and `icons`
(a mapping of built-in icon names to colors). Artwork is drawn in code, with bundled
fonts by default. The menu-bar clock is fixed authored text.

Starter pages: `appearance` (`theme`); `wifi` (`enabled`, `network`);
`displays` (`brightness`, `scale`); `sound` (`volume`, `muted`, `test`).
The sound test button records activation visually; it does not play audio.

Create custom pages using `SettingsPage(id, title, controls)` and
`Control(id, label, kind, value, options=(), minimum=0, maximum=100)`.
Kinds are `toggle`, `slider`, `choice`, `text`, and `button`. Supply the complete page
sequence with `pages=...`, or extend `starter_pages()`. Control values are validated.
Use `scroll(..., window="settings")` for a long control list.

## Embedding and excerpts

`OSClip(..., mode="desktop", width=1920, height=1080)` supplies the whole desktop.
`mode="finder"` or `mode="settings"`, with a 1280×800 viewport, supplies an isolated
window with transparent surroundings. Use ordinary `position`, `scale`, masks,
opacity, groups, and scene animations. Cursor artwork shares the same transform.
The export format stays unchanged; isolated RGBA surfaces composite into your scene.

Viewports reserve room for readable controls: isolated windows need at least 960×600;
use at least 980×690 for a desktop. Visible Finder/settings windows need 900×540. Smaller on-screen placements
use component `scale`, not a smaller design viewport. Labels are ellipsized; file
contents are clipped to the visible rows. Keep the UI large enough for your audience.

`source_start` begins playback partway through a script. Playback uses
`source_start + component age`; final state holds after the last action. In core,
explicitly wait for the desired scene duration. Ranged export and out-of-order frame
requests reproduce the same frames without replaying host actions.

This release includes one starter File/context menu, the documented settings pages,
and authored files. Spotlight, notifications, Control Center, terminal emulation,
real filesystem imports, and live OS control are outside this release.

Import the UI APIs from `faceless_champ.os_ui`; no optional dependency is needed.
The [premium opening draft](../examples/programming/hello_world/README.md) composes
an isolated Finder window with CodingChamp and FlowChamp. It is not yet rendered.
