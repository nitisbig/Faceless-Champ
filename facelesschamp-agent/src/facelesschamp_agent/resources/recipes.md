# Reusable explanatory recipes

Recipes work in kit without installing agent. Content is validated by `validate_recipe`; `apply_recipe(segment, id, content, bounds=None, events=())` returns named handles. Events use scene-local seconds and never silently extend a scene. Custom compositions can use the same public kit/core APIs.

```python
from facelesschamp_kit import apply_recipe

handles = apply_recipe(segment, "process-flow", {"steps": ["Input", "Transform", "Output"]})
```

Code/result consumes an explicitly prepared playground; rendering never executes checkpoints. Thumbnails and four-second motion previews are bundled under `resources/previews/`. They show illustrative data.

## process-flow

Explain ordered steps through progressive disclosure

Avoid: Use request-journey when movement is the point.

Targets: diagram

```json
{
  "steps": [
    "Collect",
    "Transform",
    "Deliver"
  ]
}
```

## request-journey

Follow a request through connected services

Avoid: Do not imply measured latency without real data.

Targets: diagram

```json
{
  "steps": [
    "Client",
    "Cache",
    "Database"
  ]
}
```

## before-after

Contrast a specific change

Avoid: Avoid unrelated comparisons or dense paragraphs.

Targets: before, after

```json
{
  "before": "Every request repeats the work",
  "after": "Repeated requests reuse the result"
}
```

## cause-effect

Explain cause, mechanism, and consequence

Avoid: Do not present correlation alone as causation.

Targets: diagram

```json
{
  "cause": "More requests",
  "mechanism": "Shared cache",
  "effect": "Less repeated work"
}
```

## metric-context

Give a number meaning through context

Avoid: Always state units and source or mark illustrative values.

Targets: metric, value, context

```json
{
  "value": 80,
  "label": "Requests served from cache",
  "context": "Illustrative: 80 out of 100 requests avoid repeated database work"
}
```

## annotated-trend

Explain a change in a time series

Avoid: Use ordered x values and explain units.

Targets: chart, annotation

```json
{
  "points": [
    [
      0,
      2
    ],
    [
      1,
      3
    ],
    [
      2,
      6
    ],
    [
      3,
      7
    ]
  ],
  "label": "Illustrative throughput",
  "annotation": "Capacity increases after the change"
}
```

## part-whole

Explain how parts contribute to one total

Avoid: Use nonnegative comparable values; keep the number of categories small.

Targets: chart

```json
{
  "parts": {
    "Compute": 55,
    "Storage": 30,
    "Network": 15
  }
}
```

## hierarchy

Reveal an explicit parent-child hierarchy by level

Avoid: Use explicit parents; cyclic graphs need a custom FlowCanvas.

Targets: diagram

```json
{
  "nodes": [
    {
      "id": "root",
      "label": "System",
      "parent": null
    },
    {
      "id": "a",
      "label": "Application",
      "parent": "root"
    },
    {
      "id": "b",
      "label": "Storage",
      "parent": "root"
    },
    {
      "id": "c",
      "label": "Cache",
      "parent": "b"
    }
  ]
}
```

## code-result

Connect a prepared code checkpoint to its visual result

Avoid: Prepare complete checkpoints explicitly. Intermediate edits never execute.

Targets: editor, canvas, output

```json
{
  "prepared": ".playground-cache/prepared-example"
}
```

## overview-detail

Establish context, emphasize one part, return to the overview

Avoid: Keep the same object identity and spatial context during focus.

Targets: diagram, detail

```json
{
  "steps": [
    "Input",
    "Cache",
    "Output"
  ],
  "focus": 1,
  "detail": "The cache retains results for repeated requests"
}
```
