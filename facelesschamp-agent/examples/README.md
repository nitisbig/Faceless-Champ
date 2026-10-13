# Editable production examples

Run from any directory after installing the packages:

```python
from facelesschamp_agent.examples import create_example
project = create_example("my-system", "narrated-system")
project.validate()
project.storyboard()
preview = project.preview(start=0, end=3)
project.verify(preview["artifacts"][0]["path"])
# Inspect the returned media and record review before final delivery.
result = project.render()
```

Choose `narrated-system`, `chart-explanation`, or `code-result`. Destinations must not
exist. The code example explicitly prepares a deterministic Python checkpoint when
created; subsequent rendering replays it. Install the core `coding` extra for code
examples. The narrated example copies the kit's bundled synthetic demonstration
speech and original cue timings. Chart numbers are illustrative. The chart/code
examples have no voiceover and remain silent drafts.

Generated projects contain an editable plan, ordinary Python, a narration script,
asset brief, and standard kit configuration. `scripts/release_evidence.py` renders
all recipe previews and these three complete examples. It uses native 1080p/30fps
with antialias=1 for the final fixtures; the normal starter keeps antialias=2.
