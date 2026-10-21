"""Tools for external video-authoring agents. No model service is required."""

from .errors import AgentError
from .models import (
    BeatSelection,
    DesignSpec,
    QualityReport,
    ReviewFinding,
    ScenePlan,
    SelectionPlan,
    StoryPlan,
    VideoBrief,
    VideoPlan,
)

__version__ = "2.0.0rc1"
__all__ = [
    "AgentError",
    "AgentProject",
    "BeatSelection",
    "CapabilityRegistry",
    "DesignSpec",
    "QualityReport",
    "ReviewFinding",
    "ScenePlan",
    "SelectionPlan",
    "StoryPlan",
    "VideoBrief",
    "VideoPlan",
    "install_coding_tutorial",
    "load_coding_tutorial",
    "plan_project",
    "read_project_context",
    "select_scenes",
]


def __getattr__(name):
    if name in {"load_coding_tutorial", "install_coding_tutorial"}:
        from . import templates

        return getattr(templates, name)
    if name == "read_project_context":
        from .context import read_project_context

        return read_project_context
    if name in {"select_scenes", "plan_project"}:
        from . import planning

        return getattr(planning, name)
    if name == "AgentProject":
        from .project import AgentProject

        return AgentProject
    if name == "CapabilityRegistry":
        from .registry import CapabilityRegistry

        return CapabilityRegistry
    raise AttributeError(name)
