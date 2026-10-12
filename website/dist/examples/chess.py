from faceless_champ import Canvas, ChessChamp, ChessScript, ChessTheme, Scene

class ChessDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1280, 720, "#000000"))

    def construct(self):
        script = ChessScript.from_dict({
            "schema_version": 1, "duration": 6,
            "players": {"white": "White", "black": "Black"},
            "moves": [
                {"at": 1, "duration": .5, "uci": "e2e4"},
                {"at": 2.5, "duration": .5, "uci": "d7d5"},
                {"at": 4, "duration": .5, "uci": "e4d5"},
            ],
            "annotations": [
                {"type": "text", "at": 0, "duration": 6,
                 "text": "e4 / d5 / exd5"},
                {"type": "highlight", "at": 3, "duration": 1,
                 "squares": ["e4", "d5"]},
            ],
        })
        self.add(ChessChamp(script, theme=ChessTheme(background="#000000"), width=1280, height=720, position=(640, 360)))
        self.wait(script.duration)
