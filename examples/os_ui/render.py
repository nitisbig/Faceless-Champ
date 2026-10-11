"""Run: faceless-champ render examples/os_ui/render.py Tutorial -o output/os-ui.mp4"""

from faceless_champ import Scene
from faceless_champ.os_ui import File, Folder, OSClip, OSScript, VirtualFileSystem


class Tutorial(Scene):
    def construct(self):
        filesystem = VirtualFileSystem(
            Folder(
                "home",
                "Home",
                (
                    Folder(
                        "documents",
                        "Documents",
                        (
                            File("notes", "Notes.txt", "Organize an idea.\nPresent the process."),
                            Folder("archive", "Archive"),
                        ),
                    ),
                ),
            )
        )
        script = (
            OSScript()
            .wait(1)
            .open_folder("documents")
            .rename("notes", "Launch Notes.txt")
            .drag("notes", "archive")
            .open_folder("archive")
            .preview("notes")
            .wait(1)
            .window("preview", "close")
            .open_settings()
            .set_value("appearance:theme", "dark")
            .open_settings("sound")
            .set_value("sound:volume", 40)
            .wait(1)
        )
        self.add(OSClip(filesystem, script, position=(960, 540)))
        self.wait(script.duration)
