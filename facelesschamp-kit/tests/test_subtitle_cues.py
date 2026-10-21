import pytest
from faceless_champ import SubtitleTrack, parse_srt_cues

from facelesschamp_kit import read_subtitle_cues


def test_raw_source_cues_keep_overlap_whitespace_and_source_ids():
    source = "\ufeff7\r\n00:00:00,000 --> 00:00:01,001\r\n  First\r\nline\r\n\r\n9\r\n00:00:01,000 --> 00:00:02,000\r\nSecond\r\n"
    cues = read_subtitle_cues(source)
    assert cues == parse_srt_cues(source)
    assert cues[0].text == "  First\nline" and cues[0].end == 1.001 and cues[1].start == 1
    assert [c.index for c in cues] == [7, 9]
    with pytest.raises(ValueError, match="overlap"):
        SubtitleTrack(cues)
    assert SubtitleTrack(cues, overlap_tolerance=0.001).cues == cues
