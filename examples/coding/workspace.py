"""The saved coding design. Explicit render: faceless-champ render <file> FunctionWorkspace -q ql."""

from dataclasses import replace

from faceless_champ import Animation, Canvas, CodeReveal, CodeWorkspaceDesign, CodingChamp, Scene, linear


class FunctionWorkspace(Scene):
    def __init__(self):
        self.design = CodeWorkspaceDesign.named("clean-flow")
        super().__init__(Canvas(1920, 1080, self.design.background))

    def construct(self):
        design = self.design
        box = design.code_bounds
        code = CodingChamp(
            'def greet():\n    print("Hello, Python!")\n\ngreet()',
            language="python",
            theme=design.theme,
            chrome=False,
            font_size=design.code_size,
            padding=8,
            width=box.width,
            height=box.height,
            position=(box.left, box.top),
            anchor="top_left",
        )
        editor = design.window(design.editor_full, "functions.py", children=(code,), fullscreen=True)
        self.add(editor)
        self.play(CodeReveal(code), run_time=3)
        self.wait(0.5)
        self.play(
            design.editor_motion(editor, running=True),
            *design.editor_corners(editor, running=True),
            run_time=design.shrink_duration,
        )

        box = design.terminal_bounds
        command = CodingChamp(
            "$ python functions.py",
            language="text",
            theme=design.theme,
            chrome=False,
            line_numbers=False,
            font_size=design.terminal_size,
            padding=0,
            width=box.width - 56,
            height=66,
            position=(box.left + 28, box.top + 96),
            anchor="top_left",
            opacity=0,
        )
        output = CodingChamp(
            "Hello, Python!",
            language="text",
            theme=replace(design.theme, foreground="#B1D7AD"),
            chrome=False,
            line_numbers=False,
            font_size=design.terminal_size,
            padding=0,
            width=box.width - 56,
            height=400,
            position=(box.left + 28, box.top + 176),
            anchor="top_left",
            opacity=0,
        )
        terminal = design.window(box, "Terminal", children=(command, output))
        self.play(design.terminal_in(terminal), run_time=design.terminal_entrance_duration)
        self.play(
            Animation(command, {"opacity": 1, "reveal": 1}, {"opacity": 1, "reveal": 0}, rate_func=linear), run_time=1.4
        )
        self.play(output.animate.opacity_to(1), run_time=0.15)
        self.wait(1.5)
        self.play(design.terminal_out(terminal), run_time=design.terminal_exit_duration)
        self.remove(terminal)
        self.play(
            design.editor_motion(editor, running=False),
            *design.editor_corners(editor, running=False),
            run_time=design.restore_duration,
        )
        self.wait(1)
