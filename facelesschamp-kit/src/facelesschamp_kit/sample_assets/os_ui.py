"""A complete offline tutorial. Replace the authored tree and script with your story."""

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import OSWalkthrough
from facelesschamp_kit.desktop import File, Folder, OSScript, VirtualFileSystem


def tutorial():
    filesystem = VirtualFileSystem(
        Folder(
            "home",
            "Home",
            (
                Folder(
                    "documents",
                    "Documents",
                    (
                        File(
                            "notes",
                            "Project Notes.txt",
                            "A clear idea starts with a little organization.\nBuilt with Faceless Champ.",
                        ),
                        File(
                            "outline",
                            "Presentation Outline.txt",
                            "Introduce the idea.\nShow the steps.\nCelebrate the result.",
                        ),
                        Folder("archive", "Archive"),
                    ),
                ),
                Folder("downloads", "Downloads"),
                Folder("pictures", "Pictures"),
            ),
        )
    )
    script = (
        OSScript()
        .wait(1)
        .open_folder("documents")
        .select("notes")
        .rename("notes", "Launch Notes.txt")
        .preview("notes")
        .wait(1)
        .window("preview", "close")
        .create_folder("project", "New Project")
        .drag("notes", "project")
        .open_folder("project")
        .wait(1)
        .back()
        .set_view("list")
        .right_click("outline")
        .click("menu:open")
        .wait(1)
        .window("preview", "close")
        .trash("outline", confirm=True)
        .confirm()
        .open_trash()
        .restore("outline")
        .back()
        .open_settings("appearance")
        .set_value("appearance:theme", "dark")
        .wait(1)
        .open_settings("sound")
        .set_value("sound:volume", 35)
        .set_value("sound:muted", True)
        .window("settings", "minimize")
        .window("settings", "restore")
        .window("settings", "close")
        .window("finder", "maximize")
        .wait(1)
        .window("finder", "maximize")
        .wait(1)
    )
    return filesystem, script


def build(ctx):
    filesystem, script = tutorial()
    video = Video(ctx)
    with video.segment("os-tutorial", duration=script.duration) as segment:
        segment.add(OSWalkthrough(filesystem, script))
    return video
