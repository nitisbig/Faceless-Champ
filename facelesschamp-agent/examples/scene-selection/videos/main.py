from facelesschamp_agent import AgentProject
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
