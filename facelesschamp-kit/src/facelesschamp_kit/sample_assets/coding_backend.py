"""Real Python results drive the flow, data, and tensor views."""

from faceless_champ import CanvasItem, CodeCheckpoint, EventBinding, PlaygroundScript, ValueBinding

from facelesschamp_kit.templates import coding_playground

SOURCE = """import faceless_champ.playground.runtime as pg

request = [1, 2, 3]
weights = [[1, 0, 1], [0, 1, 0]]
pg.event("request")
result = [sum(a*b for a, b in zip(row, request))
          for row in weights]
pg.event("computed")
pg.emit("input", request)
pg.emit("weights", weights)
pg.emit("result", result)
pg.emit("count", len(result))
print("Response:", result)
"""


def script():
    return PlaygroundScript(
        [
            CodeCheckpoint("first", {"api.py": SOURCE}, "api.py", "api.py", 0, 1, 1),
            CodeCheckpoint(
                "second", {"api.py": SOURCE.replace("[1, 2, 3]", "[3, 2, 4]")}, "api.py", "api.py", 2.5, 4, 4
            ),
        ],
        duration=6,
        mode="backend",
        items=[
            CanvasItem("request", "flow", "Request"),
            CanvasItem("server", "flow", "Server"),
            CanvasItem("database", "flow", "Database"),
            CanvasItem("input", "vector", "Input"),
            CanvasItem("weights", "matrix", "Weights"),
            CanvasItem("result", "collection", "Response"),
            CanvasItem("count", "variable", "Count"),
        ],
        bindings=[ValueBinding(key, key) for key in ("input", "weights", "result", "count")],
        events=[
            event
            for checkpoint, at in (("first", 1.1), ("second", 4.1))
            for event in (
                EventBinding(checkpoint, "request", "request", at, 0.6, "server"),
                EventBinding(checkpoint, "computed", "server", at + 0.6, 0.6, "database"),
            )
        ],
    )


def build(ctx):
    return coding_playground(ctx, script())
