"""Small, editable starter. The external agent replaces its example content."""

from .models import VideoPlan

INITIAL_PLAN = VideoPlan.model_validate(
    {
        "brief": {
            "title": "From idea to result",
            "prompt": "Explain a three-stage process",
            "duration": 6,
            "intended_understanding": "Each stage transforms the output of the previous stage",
        },
        "story": {
            "thesis": "A process makes an idea actionable",
            "beats": [
                {
                    "scene_id": "process",
                    "idea": "Collect, transform, deliver",
                    "purpose": "Show the ordered relationship",
                }
            ],
        },
        "scenes": [
            {
                "id": "process",
                "purpose": "Reveal an ordered process",
                "start": 0,
                "duration": 6,
                "recipe": "process-flow",
                "content": {"steps": ["Collect", "Transform", "Deliver"]},
                "visual_relationships": ["Directed edges show the order"],
                "attention_sequence": ["Input", "Transformation", "Result"],
                "key_events": [
                    {"at": 1.2, "label": "Reveal the next stage"},
                    {"at": 3.72, "label": "Emphasize result"},
                ],
                "narration": "First collect the inputs. Transform them into something useful. Then deliver the result.",
            }
        ],
    }
)

CONFIG = """schema_version = 1
[project]
name = "Agent video"
seed = 0
[videos.main]
factory = "videos.main:build"
format = "landscape"
theme = "midnight"
captions = false
[profiles.preview]
fps = 15
antialias = 1
preset = "veryfast"
[profiles.final]
fps = 30
antialias = 2
preset = "medium"
"""

SOURCE = """from facelesschamp_agent import AgentProject
from facelesschamp_kit.recipes import apply_recipe


def build(ctx):
    project = AgentProject(ctx.root)
    plan = project.plan
    video = project.new_video(ctx)
    for scene in plan.scenes:
        segment = video.segment(scene.id, start=scene.start, duration=scene.duration)
        # Replace or extend this Python composition for custom scene treatments.
        if scene.treatment != "recipe":
            raise ValueError(f"Author the custom scene {scene.id!r} in videos/main.py")
        apply_recipe(segment, scene.recipe, scene.content)
    return video
"""
