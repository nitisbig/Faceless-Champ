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

__version__ = "0.1.0rc2"
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
    "plan_project",
    "read_project_context",
    "select_scenes",
]


def __getattr__(name):
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
