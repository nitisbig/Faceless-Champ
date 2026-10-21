"""Raw source-clock subtitle cues shared by production clients."""

from faceless_champ import SubtitleCue, parse_srt_cues


def read_subtitle_cues(text: str) -> tuple[SubtitleCue, ...]:
    """Preserve raw cue times and intentional overlaps; apply no retiming."""
    return parse_srt_cues(text)
