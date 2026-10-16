# Choosing visual treatments

Premium defaults fill unspecified choices: landscape 1920×1080 at 30 fps (or
1080×1920 when shorts is requested), clean-flow theme with its packaged DM Sans,
body 44 px, heading 76 px, minimum 24 px, spacing 28 px, safe margin 64 px,
0.6-second meaningful motion, restrained color and no automatic captions. Keep
one idea and focal change per beat; use a settled hold, aligned geometry and
negative space. Do not treat this as a requirement for every scene to have a title,
card, heading, transition or subtitle. User instructions override every design
default, including these. Layout checks still report actual geometry problems.

Select one coherent theme family for the video: midnight for high-contrast technical
diagrams, light for editorial/data explanations, whiteboard for drawn explanations,
or clean-flow for a warm gray dashboard with rounded white cards and an orange accent.
These are starting points, not mandatory mappings. Record the reason in DesignSpec.
Apply shared typography, semantic colors and motion timing through new_video(ctx).

Clean-flow uses packaged DM Sans at weight 700 for headings and 400 for body text,
soft card shadows, a subtle dot grid, dark code panels, and peach highlights.
Omit DesignSpec.font to retain the theme font; supplying a custom font clears the
theme's variable-font weights. Apply the same palette to local HTML before capture.

Kit placements default to enter="theme" and exit="theme". Clean-flow resolves both
to a smooth 0.6-second "flow" reveal, moving 24 pixels upward while changing opacity.
Nested groups reveal in stable order and leave in reverse order; scripted viewports
keep their internal animation. Pass enter=None or exit=None to disable either side.
For scene continuity, retain one background and overlap outgoing/incoming content
for 0.6 seconds centered on a major boundary. Explicit durations must fit the
placement lifetime and entrance/outro windows must not overlap.

Use relationships that carry meaning: position for sequence, edges for dependency,
length for magnitude, repeated objects for quantity, and motion for a process.
Prefer sparse labels beside the relevant visual. A narrated explanation rarely needs
the same sentence displayed as a paragraph. Captions are an explicit audience choice.

Recipes: process-flow reveals sequence; request-journey follows packets; before-after
contrasts a change; cause-effect shows a mechanism; metric-context supplies meaning;
annotated-trend highlights a change; part-whole compares contributions; hierarchy
reveals explicit parent relationships; code-result pairs prepared code and output;
overview-detail retains context while emphasizing a part.

Keep spatial identity across related shots, give new information time to settle,
and use emphasis for the currently explained subject. Every transition should preserve
or deliberately reset context. A complex scene can be split instead of shrinking
labels. Inspect at the intended viewing size, including portrait layout.

For data, put units, scope and a concise source or illustrative label on screen.
Core bounding boxes are conservative: intended overlays and background panels can
intersect. Judge geometry findings using the rendered image and the scene's purpose.

For coding tutorials without custom design or instructions, use the approved
coding-tutorial pack returned by plan. The project copy has editable style.json
and TEMPLATE.md. Custom design or instructions bypass this fallback. Read the
guide before authoring; keep source/audio/timing lesson-local, and use
load_coding_tutorial(ctx.root) plus template.group(..., bounds=bounds).
