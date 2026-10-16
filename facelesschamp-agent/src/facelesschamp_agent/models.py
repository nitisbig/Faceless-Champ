"""Versioned authoring and review contracts; Python remains executable authoring."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Id = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")]
Seconds = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Status = Literal["pending", "passed", "failed", "unverified", "not_applicable"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class NarrationInput(Record):
    audio: Text | None = None
    subtitles: Text | None = None
    overlap_tolerance: Seconds = 0

    @model_validator(mode="after")
    def paired(self):
        if self.subtitles and not self.audio:
            raise ValueError("Subtitles require a supplied audio file")
        return self


class AssetInput(Record):
    id: Id
    path: Text
    kind: Literal["image", "audio", "subtitle", "font", "data", "prepared", "mesh"] = "image"
    required: bool = True
    description: Text = "Supplied project asset"
    source: str = ""


class VideoBrief(Record):
    title: Text
    prompt: Text
    audience: Text = "General audience"
    intended_understanding: Text
    format: Literal["landscape", "shorts"] = "landscape"
    duration: Positive
    delivery: Literal["full", "preview"] = "full"
    constraints: list[Text] = Field(default_factory=list)
    narration: NarrationInput = Field(default_factory=NarrationInput)
    assets: list[AssetInput] = Field(default_factory=list)
    repair_limit: Annotated[int, Field(ge=0, le=10, strict=True)] = 3


class DesignSpec(Record):
    template: Literal["coding-tutorial"] | None = None
    theme: Literal["midnight", "light", "whiteboard", "clean-flow"] = "midnight"
    rationale: Text = "High contrast with a restrained accent and readable labels"
    font: Text | None = None
    palette: dict[str, str] = Field(default_factory=dict)
    semantic_colors: dict[str, str] = Field(default_factory=dict)
    body_size: Positive = 44
    minimum_font_size: Positive = 24
    heading_size: Positive = 76
    spacing: Seconds = 28
    motion_duration: Positive = 0.6
    motion: Text = "Reveal relationships progressively and emphasize the narrated subject"
    captions: bool = False

    @model_validator(mode="after")
    def sizes(self):
        from PIL import ImageColor

        if self.minimum_font_size > min(self.body_size, self.heading_size):
            raise ValueError("Minimum font size exceeds body or heading size")
        if set(self.palette) - {"background", "surface", "foreground", "muted", "accent"}:
            raise ValueError("Unknown palette role")
        for color in (*self.palette.values(), *self.semantic_colors.values()):
            ImageColor.getcolor(color, "RGBA")
        return self


class StoryBeat(Record):
    scene_id: Id
    idea: Text
    purpose: Text


class StoryPlan(Record):
    thesis: Text
    beats: list[StoryBeat] = Field(min_length=1)


class KeyEvent(Record):
    at: Seconds
    label: Text
    target: str | None = None
    duration: Seconds = 0


class ScenePlan(Record):
    id: Id
    purpose: Text
    start: Seconds
    duration: Positive
    treatment: Literal["recipe", "custom"] = "recipe"
    recipe: str | None = None
    content: dict = Field(default_factory=dict)
    visual_relationships: list[Text] = Field(default_factory=list)
    attention_sequence: list[Text] = Field(default_factory=list)
    key_events: list[KeyEvent] = Field(default_factory=list)
    required_assets: list[Id] = Field(default_factory=list)
    narration: str = ""
    sources: list[Text] = Field(default_factory=list)
    illustrative: bool = False
    capabilities: list[Text] = Field(default_factory=list)
    selection_rationale: str = ""
    composition: str = ""
    motion_plan: str = ""
    transition: str = ""
    layout_strategy: str = ""
    intentional_overlaps: list[tuple[Text, Text]] = Field(default_factory=list)
    allow_bleed: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_recipe_and_events(self):
        if self.treatment == "recipe":
            from facelesschamp_kit.recipes import validate_recipe

            validate_recipe(self.recipe, self.content)
        elif self.recipe is not None:
            raise ValueError("Custom scenes must not declare a recipe")
        for event in self.key_events:
            if event.at >= self.duration or event.at + event.duration > self.duration + 1e-9:
                raise ValueError("Key event exceeds scene duration")
        if self.recipe in {"metric-context", "annotated-trend", "part-whole"} and not (
            self.sources or self.illustrative
        ):
            raise ValueError("Data scenes require sources or illustrative=true")
        return self


class VideoPlan(Record):
    schema_version: Literal[1] = 1
    video_id: Id = "main"
    brief: VideoBrief
    story: StoryPlan
    scenes: list[ScenePlan] = Field(min_length=1)
    design: DesignSpec = Field(default_factory=DesignSpec)

    @model_validator(mode="after")
    def references_and_timing(self):
        ids = [scene.id for scene in self.scenes]
        assets = [asset.id for asset in self.brief.assets]
        if len(set(ids)) != len(ids) or len(set(assets)) != len(assets):
            raise ValueError("Scene and asset IDs must be unique")
        if [beat.scene_id for beat in self.story.beats] != ids:
            raise ValueError("Story beats must reference each scene once in scene order")
        if [s.start for s in self.scenes] != sorted(s.start for s in self.scenes):
            raise ValueError("Scenes must be ordered by source start")
        for scene in self.scenes:
            if scene.start + scene.duration > self.brief.duration + 1e-6:
                raise ValueError(f"Scene {scene.id} exceeds the brief duration")
            if set(scene.required_assets) - set(assets):
                raise ValueError(f"Scene {scene.id} references an unknown asset")
        return self


class ReviewFinding(Record):
    scene_id: Id
    source_time: Seconds
    element: str | None = None
    severity: Literal["info", "warning", "error"] = "warning"
    code: Id = "VISUAL_REVIEW"
    observed: Text
    evidence_artifact: Text
    suggested_repair: Text


class ReviewSubmission(Record):
    schema_version: Literal[1] = 1
    fingerprint: Text
    reviewer: Text
    kind: Literal["visual", "editorial"]
    status: Literal["passed", "failed", "unverified"]
    evidence_artifacts: list[Text] = Field(default_factory=list)
    reviewed_scenes: list[Id] = Field(default_factory=list)
    findings: list[ReviewFinding] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def evidence(self):
        if self.status != "unverified" and (not self.evidence_artifacts or not self.reviewed_scenes):
            raise ValueError("A completed review requires evidence artifacts and reviewed scenes")
        if self.status == "passed" and any(f.severity == "error" for f in self.findings):
            raise ValueError("A passed review cannot contain unresolved errors")
        return self


class QualityReport(Record):
    schema_version: Literal[1] = 1
    fingerprint: str
    structural_validation: Status = "pending"
    layout_validation: Status = "pending"
    preview_media_verification: Status = "pending"
    full_export_media_verification: Status = "pending"
    visual_review: Status = "pending"
    editorial_review: Status = "pending"
    narration_alignment: Status = "pending"
    draft: bool = True
    draft_reasons: list[str] = Field(default_factory=list)
    findings: list[ReviewFinding] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)
    repair_passes: dict[str, int] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)


class HumanScores(Record):
    clarity: Annotated[int, Field(ge=1, le=5, strict=True)]
    accuracy: Annotated[int, Field(ge=1, le=5, strict=True)]
    pacing: Annotated[int, Field(ge=1, le=5, strict=True)]
    visual_quality: Annotated[int, Field(ge=1, le=5, strict=True)]
    reviewer: Text
    notes: Text


class BenchmarkResult(Record):
    schema_version: Literal[1] = 1
    prompt_id: Id
    agent: Text
    model: Text
    outcome: Literal["complete", "incomplete", "failed"]
    completion_seconds: Seconds
    repair_count: Annotated[int, Field(ge=0, strict=True)] = 0
    cost_usd: Seconds | None = None
    failures: list[Text] = Field(default_factory=list)
    artifact_paths: list[Text] = Field(default_factory=list)
    quality: QualityReport | None = None
    human_scores: HumanScores | None = None


class BeatSelection(Record):
    """A directing brief, deliberately separate from executable recipe content."""

    scene_id: Id
    start: Seconds
    duration: Positive
    narration: str
    cue_ids: list[str] = Field(default_factory=list)
    purpose: Text
    intent: Text
    evidence: list[Text]
    candidates: list[dict]
    selected_capability: Text | None = None
    selection_rationale: Text
    composition: Text
    motion: Text
    transition: Text
    attention_sequence: list[Text]
    required_inputs: list[Text]
    layout_checks: list[Text]
    requires_authoring: Literal[True] = True


class SelectionPlan(Record):
    schema_version: Literal[1] = 1
    context_fingerprint: Text
    registry_fingerprint: Text
    request_fingerprint: Text
    prompt: Text
    instructions: list[Text] = Field(default_factory=list)
    format: Literal["landscape", "shorts"] = "landscape"
    duration: Positive
    timing: Literal["source", "estimated"]
    design: DesignSpec
    guidelines: dict
    sources: list[dict]
    beats: list[BeatSelection] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)
    editorial_review: Literal["pending"] = "pending"

    @model_validator(mode="after")
    def coverage(self):
        end = 0.0
        ids = set()
        for beat in self.beats:
            if beat.scene_id in ids or abs(beat.start - end) > 1e-6:
                raise ValueError("Selection beats must be unique and cover the clock contiguously from zero")
            ids.add(beat.scene_id)
            end = beat.start + beat.duration
        if abs(end - self.duration) > 1e-6:
            raise ValueError("Selection beats must cover the complete duration")
        return self


SCHEMAS = {
    cls.__name__: cls
    for cls in (
        VideoPlan,
        VideoBrief,
        StoryPlan,
        ScenePlan,
        DesignSpec,
        QualityReport,
        ReviewFinding,
        ReviewSubmission,
        BenchmarkResult,
        BeatSelection,
        SelectionPlan,
    )
}
