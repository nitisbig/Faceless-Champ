# Prepared PR: deterministic spring motion

**Local only, as requested by the user. No branch was pushed and no GitHub PR
was opened.** This is a ready-to-use review description.

- Title: **Add deterministic spring easing with safe transforms and scheduling**
- Repository, if publication is later authorized: `nitisbig/Faceless-Champ`
- Head: `codex/spring-motion-v1`; base: `facelesschamp-agent`
- Audited base: `d61fe16594e4f46358f61cb5bca86a982d3b77da`
- Implementation commit: `bab707894d4c171bd8cb939f91bbe854c29cdf83`

## Description

Add analytical `Spring(stiffness=180, damping=23, mass=1)` easing through the
existing Scene/Animation/Track system. Underdamped, critical, and overdamped
responses support arbitrary timestamps, exact endpoints, and a certified settling
horizon retimed to the requested animation duration.

Position, rotation, and safe uniform/axis scales work on components and Groups.
Every resolved segment is validated for finite arithmetic and continuous scale
safety before publication. Schedules preserve spring validation through ping-pong
reversal and representable endpoint alignment. Generic easing behavior and
runtime Track evaluation remain unchanged. No runtime dependencies or alternate
animation/scheduling system are added.

```python
from faceless_champ import Spring

scene.play(card.animate.move_to(700, 270).scale_to(1.1),
           run_time=0.8, rate_func=Spring())
```

## Validation

- **1,574 passed, 2 skipped**: full core 1,272, six new release cases, kit 255,
  agent 41. The two unchanged skips are opt-in Chromium integrations.
- Ruff, formatting for all 12 feature Python files, and whitespace checks passed.
  Four unrelated formatter failures match the documented baseline.
- Exact states/pixels match at 17 timestamps after 18 source seek workloads at
  24/30/60 fps, across all regimes and cache modes. Sources remain unchanged.
- Numerical/safety/rollback review found no actionable defect. Independent Decimal
  and analytical references cover near-critical limits, extrema, tiny starts,
  overflow, unsafe scale paths, and failures in later nested/reversed children.
- Offline wheel/sdist builds and isolated installed-wheel CPU/ping-pong smoke passed.
- Spring and complete lower-resolution legacy previews passed FFprobe, full decode,
  source/decoded comparisons, and storyboard inspection.

See [verification](spring-motion-verification.md#phase-5-final-checks),
[raw release evidence](spring-motion-release.json), and
[usage/safety guide](motion-graphics.md#spring-motion).

## Preview and performance

Local preview: `output/spring_motion/preview.mp4`, 10 seconds, 960×540, 30 fps,
300 silent H.264 frames. Storyboard:
`output/spring_motion/storyboard/storyboard.png`. Regenerate with:

```bash
.venv/bin/python examples/spring_motion/render.py --frames --overwrite
.venv/bin/python examples/spring_motion/verify.py --output output/spring_motion/phase5/fps-verification.json
.venv/bin/python examples/spring_motion/benchmark.py --frames 180 --repeats 7 --output output/spring_motion/phase5/benchmark-final.json
```

Local 12-card static/smooth/spring/identical-trajectory-control medians were
1.111/3.560/4.248/3.466 ms/frame. A Spring evaluation measured 3.826 µs. The
0.688 ms point difference versus smooth is 19.3%; raw trials show substantial
variation. No zero-cost or universal percentage-overhead guarantee is claimed.

## Limits

Certification covers local transforms, not global canvas containment. Keep
opacity/color/reveals on independent conventional easings. There is no initial
velocity, live retargeting, velocity handoff, or coupled constraints. The legacy
demo is verified at 480×270/24 fps/AA1; its original 960×540/AA2 attempt and the
optional Spring 1080p export are unverified. No later motion subsystem is included.
Review and merge remain separate actions.
