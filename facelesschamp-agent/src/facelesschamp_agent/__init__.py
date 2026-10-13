"""Tools for external video-authoring agents. No model service is required."""

from .errors import AgentError
from .models import DesignSpec, QualityReport, ReviewFinding, ScenePlan, StoryPlan, VideoBrief, VideoPlan

__version__ = "0.1.0rc1"
__all__ = [
    "AgentError",
    "AgentProject",
    "CapabilityRegistry",
    "DesignSpec",
    "QualityReport",
    "ReviewFinding",
    "ScenePlan",
    "StoryPlan",
    "VideoBrief",
    "VideoPlan",
]


def __getattr__(name):
    if name == "AgentProject":
        from .project import AgentProject

        return AgentProject
    if name == "CapabilityRegistry":
        from .registry import CapabilityRegistry

        return CapabilityRegistry
    raise AttributeError(name)
