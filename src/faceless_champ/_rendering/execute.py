"""The scene walk shared by Pillow, native Skia and device compositing.

Painters own pixel operations and local surfaces. They receive evaluated entries
and a continuation for their already ordered children, never authoring tracks.
"""


def walk_frame(frame, paint, context):
    def visit(entry, current):
        if not entry.visible:
            return None

        def children(child_context, selected=None):
            for child in entry.children if selected is None else selected:
                if child.visible:
                    yield visit(child, child_context)

        return paint(entry, children, current)

    for entry in frame.roots:
        if entry.visible:
            yield visit(entry, context)
