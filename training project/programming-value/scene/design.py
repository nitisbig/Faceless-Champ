from facelesschamp_kit.themes import Theme

from faceless_champ import Bounds, Canvas

CANVAS = Canvas(1920, 1080, "#FFFFFF")
THEME = Theme(
    name="editorial",
    background="#FFFFFF",
    surface="#F4F3EE",
    foreground="#292724",
    muted="#B1ADA1",
    accent="#C15F3C",
    heading_size=88,
    body_size=44,
    minimum_font_size=28,
    spacing=28,
    radius=24,
    motion_duration=0.45,
)
TITLE = Bounds(96, 88, 1824, 260)
NOTE = Bounds(160, 282, 1760, 362)
BODY = Bounds(96, 412, 1824, 934)
LEFT = Bounds(96, 412, 912, 934)
RIGHT = Bounds(1008, 412, 1824, 934)
ACCENT, INK, SURFACE, MUTED = THEME.accent, THEME.foreground, THEME.surface, THEME.muted

CHAPTERS = (
    ("code-value", 1, 306),
    ("systems", 306, 477),
    ("optimization", 477, 620),
    ("better-questions", 620, 903),
    ("human-judgment", 903, 1102),
    ("useful-systems", 1102, None),
)
