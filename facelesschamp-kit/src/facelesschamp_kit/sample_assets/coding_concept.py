"""Edit complete revisions below, then run fc-kit prepare."""

from facelesschamp_kit.playground import CanvasItem, CodeCheckpoint, EventBinding, PlaygroundScript, ValueBinding
from facelesschamp_kit.templates import coding_playground

SOURCE = """import facelesschamp_kit.playground.runtime as pg

class Car:
    def __init__(self, color):
        self.color = color
        self.speed = 0

    def accelerate(self, amount):
        self.speed += amount

red = Car("red")
blue = Car("blue")
red.accelerate(AMOUNT)
pg.emit("red", vars(red))
pg.emit("blue", vars(blue))
pg.event("accelerate")
print("Red:", red.speed, "Blue:", blue.speed)
"""


def script():
    return PlaygroundScript(
        [
            CodeCheckpoint("create", {"cars.py": SOURCE.replace("AMOUNT", "0")}, "cars.py", "cars.py", 0, 1, 1),
            CodeCheckpoint("accelerate", {"cars.py": SOURCE.replace("AMOUNT", "40")}, "cars.py", "cars.py", 2.5, 4, 4),
        ],
        duration=6,
        mode="concept",
        items=[
            CanvasItem("red", "car", "red : Car", color="#F07985"),
            CanvasItem("blue", "car", "blue : Car", color="#76B4FF"),
        ],
        bindings=[ValueBinding("red", "red"), ValueBinding("blue", "blue")],
        events=[EventBinding("accelerate", "accelerate", "red", 4.2, 0.8)],
    )


def build(ctx):
    return coding_playground(ctx, script())
