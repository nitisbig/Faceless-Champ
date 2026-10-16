# Scene-selection example

A silent authored caching example. The SRT clock is a deterministic fixture, not
an alignment claim about recorded speech. The final 0.320 seconds are a hold.

Run from the repository's installed environment:

```bash
fc-agent --project facelesschamp-agent/examples/scene-selection plan --prompt "Explain caching using the supplied context"
python facelesschamp-agent/examples/scene-selection/render.py
```

Read both planning artifacts. Compare suggested treatments with agent-plan.json;
the authored plan deliberately refines suggestions using the full story. The renderer
checks layout and verifies a ten-second preview. It preserves draft status because
no audio was supplied. `--full` requests the full 12.320-second composition.
