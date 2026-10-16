"""Local scene-selection briefs for external authoring agents.

Ranking is explainable retrieval, not a language model or an aesthetic verdict.
Source clocks and user direction take precedence over the production defaults.
"""

import hashlib
import json
import math
import re
from copy import deepcopy
from pathlib import Path

from .context import read_project_context
from .errors import AgentError
from .models import BeatSelection, DesignSpec, SelectionPlan
from .registry import CapabilityRegistry
from .templates import TEMPLATE_ID, coding_template_guidance, default_coding_template, load_coding_tutorial

PLANNING_VERSION = 3
_PROJECT_CONFIG_LIMIT = 2 * 1024 * 1024
_CACHE_LIMIT = 64 * 1024 * 1024

PREMIUM_GUIDELINES = {
    "precedence": ["explicit user instructions", "project design and constraints", "defaults below"],
    "canvas": {"landscape": [1920, 1080], "shorts": [1080, 1920], "fps": 30},
    "composition": "One focal idea per beat; use measured safe bounds, alignment and negative space.",
    "typography": "Use the theme font, a consistent hierarchy and short labels; split density before shrinking text.",
    "color": "Use a coherent theme, one restrained accent, high contrast and stable semantic colors.",
    "motion": "Reveal cause and relationships on narration cues; preserve object identity and allow a settled hold.",
    "transition": "Use continuity or a clean cut at idea boundaries; choose decorative transitions only if requested.",
    "imagery": "Use relevant supplied artwork or public library primitives; declare missing assets visibly.",
    "text": "Use concise labels beside the subject. Captions, titles and callouts follow the user's instructions.",
    "truth": "Preserve source times, tiny overlaps, units and provenance. Mark illustrative data; never invent measurements.",
    "review": "Check boundaries, overflow and unintended overlap through motion; inspect encoded frames and a short preview.",
    "delivery": "Deliver render.py and a verified short preview; full exports require the requested delivery scope.",
}

# These are relationship signals, not a closed capability catalog. Candidate
# retrieval below always also searches the live installed registry.
_INTENTS = (
    (
        "comparison",
        r"\bbefore\b|\bafter\b|\bversus\b|\bcompared?\b|\binstead\b",
        "before-after",
        "Contrast the same subject before and after a change",
    ),
    (
        "journey",
        r"\brequest\b|\bpacket\b|\brout(?:e|ing)\b|\bclient\b|\bserver\b",
        "request-journey",
        "Follow one subject through connected stages",
    ),
    (
        "hierarchy",
        r"\bhierarch\w*\b|\bparent\b|\bchild\b|\btaxonomy\b",
        "hierarchy",
        "Reveal the parent and child relationship by level",
    ),
    (
        "trend",
        r"\btrend\b|\btime series\b|\bover time\b|\bgrew\b|\bgrowth\b",
        "annotated-trend",
        "Explain a change over time using sourced values",
    ),
    (
        "proportion",
        r"\bproportion\b|\bshare\b|\bpercent\w*\b|\bparts? of\b",
        "part-whole",
        "Show contributions to one whole using sourced values",
    ),
    (
        "code",
        r"\bcode\b|\bpython\b|\bfunction\b|\bprogram\w*\b|\bsyntax\b",
        None,
        "Connect source code with the behavior being explained",
    ),
    (
        "geometry",
        r"\bmesh\b|\bsection\b|\b3d\b|\bassembly\b|\bgeometry\b|\bstructure\b",
        "arch-design",
        "Explain spatial relationships using named geometry",
    ),
    (
        "geography",
        r"\bgeograph\w*\b|\bcountry\b|\bcontinent\b|\bglobe\b|\bmap\b",
        None,
        "Use spatial context to explain location or scale",
    ),
    (
        "mechanism",
        r"\bbecause\b|\bcaus\w*\b|\btherefore\b|\bleads? to\b|\bmechanism\b",
        "cause-effect",
        "Reveal the cause, mechanism and consequence",
    ),
    (
        "sequence",
        r"\bfirst\b|\bthen\b|\bfinally\b|\bsteps?\b|\bprocess\b",
        "process-flow",
        "Reveal the ordered relationship progressively",
    ),
    (
        "metric",
        r"\bmetric\b|\bnumber\b|\b\d+(?:\.\d+)?\s*(?:%|ms|seconds|million|billion)\b",
        "metric-context",
        "Give a sourced number context and units",
    ),
)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _groups(context, prompt, duration, target):
    cues = context.get("cues", [])
    if cues:
        source_end = max(float(c["end"]) for c in cues)
        if duration is not None and duration + 1e-9 < source_end:
            raise AgentError("SOURCE_DURATION", "Requested duration cuts off the supplied cues", source_end=source_end)
        duration = duration or max(float(context.get("duration") or 0), source_end)
        groups, current = [], []
        for cue in cues:
            if current:
                span = float(current[-1]["end"]) - float(current[0]["start"])
                gap = float(cue["start"]) - float(current[-1]["end"])
                sentence = re.search(r"[.!?][\"')]*$", current[-1]["text"].strip())
                if span >= target or (span >= target / 2 and (sentence or gap >= 0.6)):
                    groups.append(current)
                    current = []
            current.append(cue)
        if current:
            groups.append(current)
        # A final tiny cue stays with the preceding idea instead of producing a flash.
        if len(groups) > 1 and float(groups[-1][-1]["end"]) - float(groups[-1][0]["start"]) < 1:
            groups[-2].extend(groups.pop())
        starts = [0.0] + [float(g[0]["start"]) for g in groups[1:]]
        # Several long overlapping source cues can have equal starts. Merge them;
        # their original IDs/times remain in the context artifact.
        merged = []
        for start, group in zip(starts, groups, strict=True):
            if merged and start <= merged[-1][0]:
                merged[-1][1].extend(group)
            else:
                merged.append((start, group))
        result = []
        for i, (start, group) in enumerate(merged):
            end = merged[i + 1][0] if i + 1 < len(merged) else duration
            result.append((start, end - start, " ".join(c["text"] for c in group), [str(c["id"]) for c in group]))
        return result, duration, "source"
    text = context.get("narration_text") or prompt
    words = text.split()
    duration = duration or max(6.0, len(words) / 2.4)
    count = min(max(1, math.ceil(duration / target)), max(1, len(words) // 8))
    groups = []
    for i in range(count):
        chunk = words[len(words) * i // count : len(words) * (i + 1) // count]
        start, end = duration * i / count, duration * (i + 1) / count
        groups.append((start, end - start, " ".join(chunk), []))
    return groups, duration, "estimated"


def _direction(text):
    matches = []
    for order, (intent, pattern, recipe, purpose) in enumerate(_INTENTS):
        evidence = list(dict.fromkeys(m.group(0) for m in re.finditer(pattern, text, re.IGNORECASE)))
        if evidence:
            matches.append((len(evidence), -order, intent, recipe, purpose, evidence))
    if not matches:
        return (
            "overview",
            "overview-detail",
            "Establish context and focus on the narrated subject",
            ["No strong relationship signal; confirm the treatment editorially"],
        )
    _, _, intent, recipe, purpose, evidence = max(matches)
    return intent, recipe, purpose, [f"Narration contains: {word}" for word in evidence]


def _project_direction(root):
    """Read only the known project contract, including when --input narrows discovery."""
    root = Path(root).resolve()
    path = root / "agent-plan.json"
    if not path.exists() and not path.is_symlink():
        return {}, [], None, {}
    try:
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError("The project plan resolves outside the project root")
        with path.open("rb") as stream:
            raw = stream.read(_PROJECT_CONFIG_LIMIT + 1)
        if len(raw) > _PROJECT_CONFIG_LIMIT:
            raise ValueError("The project plan exceeds the safe configuration byte limit")
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, dict):
            raise TypeError("The project plan must be a JSON object")
        design, brief = data.get("design", {}), data.get("brief", {})
        if not isinstance(design, dict) or not isinstance(brief, dict):
            raise TypeError("Project design and brief must be JSON objects")
        constraints = brief.get("constraints", [])
        if not isinstance(constraints, list) or not all(isinstance(v, str) and v.strip() for v in constraints):
            raise ValueError("Project brief constraints must be nonempty strings")
        brief_duration, brief_format = brief.get("duration"), brief.get("format")
        if brief_duration is not None and (
            isinstance(brief_duration, bool)
            or not isinstance(brief_duration, (int, float))
            or not math.isfinite(brief_duration)
            or brief_duration <= 0
        ):
            raise ValueError("Project brief.duration must be finite and positive")
        if brief_format is not None and brief_format not in ("landscape", "shorts"):
            raise ValueError("Project brief.format must be landscape or shorts")
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise AgentError(
            "PROJECT_DIRECTION",
            f"Cannot read existing project direction: {exc}",
            path="agent-plan.json",
            suggested_fix="Correct agent-plan.json; keep its design/brief as JSON data and all paths inside the project",
        ) from exc
    return (
        design,
        constraints,
        {
            "path": "agent-plan.json",
            "kind": "project-plan",
            "size": len(raw),
            "checksum": hashlib.sha256(raw).hexdigest(),
            "checksum_algorithm": "sha256",
        },
        {"duration": brief_duration, "format": brief_format},
    )


def _prepare_request(
    root,
    context,
    *,
    prompt,
    instructions=(),
    design=None,
    format=None,
    duration=None,
    target_beat_seconds=7.0,
    candidate_limit=4,
):
    if not isinstance(prompt, str) or not prompt.strip():
        raise AgentError("BRIEF", "Supply a nonempty video prompt")
    if isinstance(instructions, str):
        instructions = [instructions]
    else:
        try:
            instructions = list(instructions)
        except TypeError as exc:
            raise AgentError("INSTRUCTIONS", "Instructions must be an iterable of nonempty strings") from exc
    if not all(isinstance(v, str) and v.strip() for v in instructions):
        raise AgentError("INSTRUCTIONS", "Instructions must be nonempty strings")
    if format is not None and format not in ("landscape", "shorts"):
        raise AgentError("FORMAT", "Choose landscape or shorts")
    if (
        isinstance(candidate_limit, bool)
        or not isinstance(candidate_limit, int)
        or not 1 <= candidate_limit <= 10
        or isinstance(target_beat_seconds, bool)
        or not isinstance(target_beat_seconds, (int, float))
        or not 2 <= target_beat_seconds <= 30
    ):
        raise AgentError("PLANNING_LIMIT", "Use 1..10 candidates and a 2..30 second target beat")
    if duration is not None and (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration <= 0
    ):
        raise AgentError("DURATION", "Duration must be finite and positive")
    narration_source = context.get("narration_source")
    if not context.get("cues") and any(
        source.get("path") == narration_source and source.get("text_truncated") for source in context.get("sources", [])
    ):
        raise AgentError(
            "CONTEXT_INCOMPLETE",
            "Untimed narration exceeds the context excerpt budget",
            suggested_fix="Increase --max-chars, narrow --input to the narration, or supply the complete source cues",
            path=narration_source,
        )
    project_design, constraints, config_source, project_brief = _project_direction(root)
    format = format if format is not None else project_brief.get("format") or "landscape"
    project_warnings = []
    if duration is None and project_brief.get("duration") is not None:
        duration = project_brief["duration"]
        source_end = max((float(cue["end"]) for cue in context.get("cues", [])), default=0.0)
        if duration + 1e-9 < source_end:
            project_warnings.append(
                f"Existing brief.duration ({duration:g}s) ends before the supplied cue clock ({source_end:g}s); "
                "extended planning duration to preserve the complete source clock."
            )
            duration = source_end
    if design is not None and not isinstance(design, dict):
        raise AgentError("DESIGN", "Custom design must be a partial DesignSpec JSON object")
    merged_design = {"theme": "clean-flow", **project_design, **(design or {})}
    for key in ("palette", "semantic_colors"):
        if isinstance(project_design.get(key), dict) and isinstance((design or {}).get(key), dict):
            merged_design[key] = {**project_design[key], **design[key]}
    selected_design = DesignSpec.model_validate(merged_design)
    use_template = default_coding_template(
        root=root,
        prompt=prompt,
        context=context,
        instructions=instructions,
        design=design,
        project_design=project_design,
        constraints=constraints,
        format=format,
    )
    selected_design.template = TEMPLATE_ID if use_template else None
    if use_template:
        selected_design.theme = "clean-flow"
    template = coding_template_guidance(load_coding_tutorial(root).style) if use_template else None
    return {
        "prompt": prompt,
        "instructions": instructions,
        "design": selected_design.model_dump(mode="json"),
        "format": format,
        "duration": duration,
        "target": target_beat_seconds,
        "limit": candidate_limit,
        "project_constraints": constraints,
        "project_config": config_source,
        "project_warnings": project_warnings,
        "template": template,
    }


def _terms(text):
    stop = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "are",
        "was",
        "have",
        "has",
        "not",
        "use",
        "into",
        "when",
        "then",
        "you",
        "your",
        "our",
        "its",
        "they",
        "will",
        "one",
        "can",
        "all",
    }
    return set(re.findall(r"[a-z][a-z0-9_-]{2,}", text.lower())) - stop


def _supplement_index(context):
    index = []
    for source in context.get("sources", []):
        text = source.get("text")
        if source.get("kind") not in {"data", "text", "code"} or not text or source.get("path") == "agent-plan.json":
            continue
        terms = _terms(text[:1200]) | _terms(source["path"])
        if terms:
            index.append((source["path"], terms))
    return index


def _supplement_hints(index, text):
    terms = _terms(text)
    ranked = sorted((item for item in index if terms & item[1]), key=lambda item: (-len(terms & item[1]), item[0]))[:2]
    hints, refs = [], []
    for path, words in ranked:
        # Only a bounded token summary reaches retrieval; complete text stays in context.json.
        hints.extend(sorted(words, key=lambda word: (word not in terms, word))[:24])
        refs.append(path)
    return " ".join(dict.fromkeys(hints)), refs


def _requested_treatment(registry, request):
    """Recognize explicit installed IDs and a narrow editor idiom; leave other interpretation external."""
    ids = re.compile(r"\b(?:recipe|asset|design):[^\s,;\"'`)>\]}]+|\b(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*\b")
    negative = re.compile(
        r"(?:do\s+not|don't|avoid|without|never|exclude|no)(?:\s+(?:use|using))?(?:\s+the)?$", re.IGNORECASE
    )
    decisions = {}
    directions = [*request["instructions"], request["prompt"], *request["project_constraints"]]
    for direction in directions:
        for match in ids.finditer(direction):
            capability = match.group().rstrip(".")
            if capability in decisions:
                continue
            excluded = bool(negative.search(direction[: match.start()].rstrip()))
            decisions[capability] = not excluded
    excluded = {key for key, allowed in decisions.items() if not allowed}
    for direction in directions:
        for match in ids.finditer(direction):
            capability = match.group().rstrip(".")
            if capability in excluded:
                continue
            candidates = registry.search(capability, compact=True, limit=12)
            found = next((candidate for candidate in candidates if candidate["id"] == capability), None)
            if found:
                return found, excluded, "explicit capability ID"
        editor = re.search(r"\bfull[- ]?screen\s+(?:code\s+)?editor\b", direction, re.IGNORECASE)
        if editor and not negative.search(direction[: editor.start()].rstrip()):
            for capability in ("facelesschamp_kit.blocks.CodeEditor", "faceless_champ.CodeEditor"):
                if decisions.get(capability) is False:
                    continue
                candidates = registry.search(capability, compact=True, limit=12)
                found = next((candidate for candidate in candidates if candidate["id"] == capability), None)
                if found:
                    return (
                        found,
                        excluded,
                        "full-screen editor direction",
                    )
    return None, excluded, None


def _build_selection(context, registry, manifest, request):
    prompt, instructions, format = request["prompt"], request["instructions"], request["format"]
    groups, actual_duration, timing = _groups(context, prompt, request["duration"], request["target"])
    candidate_limit = request["limit"]
    preferred, excluded, preference_reason = _requested_treatment(registry, request)
    supplements = _supplement_index(context)
    direction_hint = " ".join([*instructions, prompt, *request["project_constraints"]])[:2000]
    scenes = []
    for index, (start, length, narration, cue_ids) in enumerate(groups, 1):
        intent, recipe, purpose, evidence = _direction(narration)
        supplement_hint, supplement_refs = _supplement_hints(supplements, f"{narration} {direction_hint}")
        if intent == "overview":
            intent, recipe, purpose, evidence = _direction(f"{direction_hint} {supplement_hint}")
            evidence = [item.replace("Narration contains:", "Brief/context contains:") for item in evidence]
        query = f"{intent} {narration} {direction_hint} {supplement_hint}"
        candidates = registry.recommend(query, limit=candidate_limit)
        if request["template"] and intent == "code":
            template_id = "facelesschamp_kit.CodingTutorialTemplate"
            options = registry.search(template_id, compact=True, limit=12)
            template_candidate = next((candidate for candidate in options if candidate["id"] == template_id), None)
            if template_candidate:
                candidates = [
                    {
                        **template_candidate,
                        "score": None,
                        "reasons": ["Approved coding tutorial default; no custom design/instructions"],
                    }
                ] + [candidate for candidate in candidates if candidate["id"] != template_id]
        elif not request["template"]:
            candidates = [
                candidate
                for candidate in candidates
                if not candidate["id"].endswith((".CodingTutorialStyle", ".CodingTutorialTemplate"))
            ]
        if recipe:
            recipe_candidates = registry.search(recipe, kind="recipe", compact=True)
            chosen = next((r for r in recipe_candidates if r["id"] == f"recipe:{recipe}"), None)
            if chosen and chosen["id"] not in excluded:
                candidates = [{**chosen, "score": len(evidence), "reasons": evidence}] + [
                    c for c in candidates if c["id"] != chosen["id"]
                ]
        candidates = [candidate for candidate in candidates if candidate["id"] not in excluded]
        if preferred:
            candidates = [{**preferred, "score": None, "reasons": [f"User/project direction: {preference_reason}"]}] + [
                candidate for candidate in candidates if candidate["id"] != preferred["id"]
            ]
        candidates = candidates[:candidate_limit]
        selected = candidates[0]["id"] if candidates else None
        rationale = (
            f"{purpose}. Retrieval suggestion based on explicit narration signals; confirm against the full context."
        )
        if preferred:
            rationale += f" The requested treatment takes priority ({preference_reason})."
        if supplement_refs:
            evidence = [*evidence, *(f"Supplement reference: {path}" for path in supplement_refs)]
        required = [
            "Author content from the supplied narration and evidence; inspect describe ID for its current contract"
        ]
        if intent in {"metric", "trend", "proportion"}:
            required.append("Sourced values, labels and units; label illustrative data visibly if explicitly allowed")
        if intent == "geometry":
            required.append("Named model parts or explicitly schematic local geometry; dimensions and field provenance")
        if intent == "code":
            required.append("Complete source; explicitly prepared checkpoints only when output is shown")
        scenes.append(
            BeatSelection(
                scene_id=f"beat-{index:03d}",
                start=start,
                duration=length,
                narration=narration,
                cue_ids=cue_ids,
                purpose=purpose,
                intent=intent,
                evidence=evidence,
                candidates=candidates,
                selected_capability=selected,
                selection_rationale=rationale,
                composition=(
                    "Use the editor workspace across the full frame and fit content within measured bounds. "
                    "Follow explicit chrome, text and motion restrictions."
                    if preference_reason == "full-screen editor direction"
                    else "Arrange the subject in the measured safe area; "
                    + (
                        "stack the relationship vertically for portrait viewing"
                        if format == "shorts"
                        else "use a clear reading order with room for the focal change"
                    )
                    + ". Retain spatial anchors from the preceding beat when they carry context."
                ),
                motion="Establish context, reveal the narrated relationship on source cues, emphasize the result, then hold.",
                transition="Keep shared anchors or cut at this idea boundary; apply explicit user transition direction first.",
                attention_sequence=["Context", "Narrated relationship or change", "Result and settled hold"],
                required_inputs=required,
                layout_checks=[
                    "Canvas and safe-area boundaries",
                    "Text and child overflow",
                    "Unintended sibling overlap",
                    "Motion extrema and beat boundaries",
                    "Readable labels at the intended viewing size",
                ],
            )
        )
    warnings = [*context.get("warnings", []), *request["project_warnings"]]
    if timing == "estimated":
        warnings.append(
            "No source cue clock: beat times are estimates; replace with supplied timing before narrated delivery."
        )
    if context.get("truncated"):
        warnings.append("Context exceeds the read budget: consult referenced source files before finalizing any scene.")
    warnings.append(
        "Scene selection is a retrieval draft. The external agent must interpret, author, inspect and repair it."
    )
    guidelines = {**deepcopy(PREMIUM_GUIDELINES), "project_constraints": request["project_constraints"]}
    if request["template"]:
        guidelines["template"] = request["template"]
        guidelines["text"] = request["template"]["text"]
        for beat in scenes:
            beat.required_inputs.append(
                "Use the selected coding-tutorial design pack; supply lesson-specific code and output"
            )
            beat.composition = (
                "Use the approved coding-tutorial editor/terminal composition and visual assets. "
                "Read templates/coding-tutorial/TEMPLATE.md; choose helpers that explain this beat. "
                "No external headings or captions; maintain uniform whole-window transforms and measured safe bounds."
            )
    sources = [*context["sources"], *context.get("assets", [])]
    if request["project_config"] and not any(source["path"] == "agent-plan.json" for source in sources):
        sources.append(request["project_config"])
    return SelectionPlan(
        context_fingerprint=context["fingerprint"],
        registry_fingerprint=manifest["fingerprint"],
        request_fingerprint=_hash(request),
        prompt=prompt,
        instructions=instructions,
        format=format,
        duration=actual_duration,
        timing=timing,
        design=DesignSpec.model_validate(request["design"]),
        guidelines=guidelines,
        sources=[
            {k: s[k] for k in ("path", "kind", "checksum", "checksum_algorithm", "size") if k in s} for s in sources
        ],
        beats=scenes,
        warnings=warnings,
    )


def select_scenes(
    root=".",
    *,
    prompt,
    instructions=(),
    design=None,
    format=None,
    duration=None,
    target_beat_seconds=7.0,
    candidate_limit=4,
    context=None,
    registry=None,
):
    """Build a directing brief; supplied direction precedes project settings and defaults.

    Project configuration is read as data. General natural-language interpretation
    and final treatment approval remain the external authoring agent's work.
    """
    context = context if context is not None else read_project_context(root)
    request = _prepare_request(
        root,
        context,
        prompt=prompt,
        instructions=instructions,
        design=design,
        format=format,
        duration=duration,
        target_beat_seconds=target_beat_seconds,
        candidate_limit=candidate_limit,
    )
    registry = registry or CapabilityRegistry()
    return _build_selection(context, registry, registry.manifest(), request)


def _cache_json(path):
    with path.open("rb") as stream:
        raw = stream.read(_CACHE_LIMIT + 1)
    if len(raw) > _CACHE_LIMIT:
        raise ValueError("Planning cache exceeds its safe byte limit")
    return json.loads(raw)


def _implementation_digest():
    """Invalidate cached directing decisions when installed planning semantics change."""
    try:
        sources = {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("planning.py", "models.py", "registry.py", "context.py", "templates.py")
        }
    except OSError as exc:
        raise AgentError(
            "PLANNING_IMPLEMENTATION",
            "Cannot fingerprint the installed planning implementation",
            suggested_fix="Reinstall the complete facelesschamp-agent package, including its Python source modules",
        ) from exc
    return _hash(sources)


def plan_project(root=".", *, paths=None, max_chars=24000, **request):
    """Save bounded context/selection artifacts; return a small authoring handoff.

    Identical source, library and request fingerprints reuse the same artifact path.
    Neither agent-plan.json nor scene code is overwritten.
    """
    from .project import _write_json

    root = Path(root).resolve()
    context = read_project_context(root, paths=paths, max_chars=max_chars)
    registry = request.pop("registry", None) or CapabilityRegistry()
    original_request = request
    request = _prepare_request(root, context, **original_request)
    template = None
    if request["template"]:
        from .templates import install_coding_tutorial

        template = install_coding_tutorial(root)
        context = read_project_context(root, paths=paths, max_chars=max_chars)
        request = _prepare_request(root, context, **original_request)
    manifest = registry.manifest()
    key = _hash(
        {
            "algorithm": PLANNING_VERSION,
            "implementation": _implementation_digest(),
            "context": _hash(context),
            "request": request,
            "registry": manifest["fingerprint"],
            "defaults": PREMIUM_GUIDELINES,
        }
    )
    directory = root / ".fc-agent" / "planning" / key[:20]
    if not directory.resolve().is_relative_to(root):
        raise AgentError(
            "PLANNING_PATH", "Planning artifact directory must remain inside the project", path=str(directory)
        )
    plan_path, context_path = directory / "scene-selection.json", directory / "context.json"
    cache_path = directory / "cache.json"
    reused = False
    try:
        raw_plan, cache = _cache_json(plan_path), _cache_json(cache_path)
        plan = SelectionPlan.model_validate(raw_plan)
        reused = (
            cache == {"key": key, "selection_digest": _hash(raw_plan)}
            and _cache_json(context_path) == context
            and plan.context_fingerprint == context["fingerprint"]
            and plan.registry_fingerprint == manifest["fingerprint"]
            and plan.request_fingerprint == _hash(request)
        )
    except (OSError, ValueError):
        pass
    if not reused:
        plan = _build_selection(context, registry, manifest, request)
        raw_plan = plan.model_dump(mode="json")
        _write_json(context_path, context)
        _write_json(plan_path, raw_plan)
        _write_json(cache_path, {"key": key, "selection_digest": _hash(raw_plan)})
    return {
        "status": "ready_for_authoring",
        "selection": str(plan_path),
        "context": str(context_path),
        "reused": reused,
        "beat_count": len(plan.beats),
        "duration": plan.duration,
        "timing": plan.timing,
        "design": plan.design.model_dump(mode="json"),
        "instructions": plan.instructions,
        "template": template,
        "beats": [
            {
                "id": b.scene_id,
                "start": b.start,
                "duration": b.duration,
                "intent": b.intent,
                "selected": b.selected_capability,
            }
            for b in plan.beats
        ],
        "warnings": plan.warnings,
        "next_actions": [
            (
                "Read both context and selection artifacts, including supplied assets and source references; "
                "follow explicit user instructions before project constraints and defaults"
            ),
            "Confirm each treatment and retrieve describe only for selected IDs",
            "Write agent-plan.json and videos/main.py using exact source timing",
            "Run audit-layout, repair scoped findings, inspect storyboard and motion preview",
            "Run entrypoint, deliver render.py and a verified short preview",
        ],
    }
