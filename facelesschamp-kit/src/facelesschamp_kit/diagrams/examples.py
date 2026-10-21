"""Small editable recipes for each FlowChamp diagram family."""

from facelesschamp_kit.diagrams.model import FlowEdge, FlowGraph, FlowNode, FlowPort
from facelesschamp_kit.diagrams.script import FlowScript


def recipe(family="workflow", *, portrait=False):
    """Return a graph and six-second script; positions adapt to the canvas orientation."""
    families = {
        "workflow": (("Input", "document"), ("Process", "service"), ("Output", "document")),
        "system": (("Client", "client"), ("Service", "service"), ("Database", "database")),
        "network": (("Client", "client"), ("Router", "router"), ("Server", "server")),
        "idea-map": (("Question", "circle"), ("Explore", "diamond"), ("Insight", "rounded_rectangle")),
        "circuit": (("Battery", "battery"), ("Resistor", "resistor"), ("LED", "led")),
    }
    if family not in families:
        raise ValueError(f"Unknown diagram family: {family}")
    ports = (FlowPort("in", "left"), FlowPort("out", "right")) if family == "circuit" else ()
    nodes = tuple(
        FlowNode(f"n{i}", label, symbol, size=(160, 90), ports=ports)
        for i, (label, symbol) in enumerate(families[family])
    )
    edges = tuple(
        FlowEdge(
            f"e{i}",
            f"n{i}",
            f"n{i + 1}",
            source_port="out" if ports else None,
            target_port="in" if ports else None,
            arrows="none" if family == "circuit" else "end",
        )
        for i in range(2)
    )
    graph = FlowGraph(nodes, edges, direction="vertical" if portrait else "horizontal")
    script = FlowScript().draw(["n0", "n1", "n2"], duration=0.6, stagger=0.6)
    script.draw(["e0", "e1"], at=1.8, duration=0.5, stagger=0.5, tool="pen")
    script.signal(["e0", "e1"], at=2.8, duration=2, repeat=2, marker="packet")
    script.highlight("n1", at=3.2, duration=1.5, dim=0.3)
    script.reveal("n2", at=5, duration=1)
    return graph, script
