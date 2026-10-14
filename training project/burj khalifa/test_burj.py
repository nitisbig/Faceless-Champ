"""Content/timing invariants that would corrupt the film if they regressed."""

from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
from facelesschamp_kit import Project
from scene.model import geometry
from scene.story import CHAPTERS, DURATION, MOTION_END, TRACK

from faceless_champ import ArchChamp, SubtitleTrack

PROJECT = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def compiled():
    return Project(PROJECT).build()


def test_cues_master_audio_and_contiguous_chapters(compiled):
    original = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt", overlap_tolerance=0.001)
    assert len(original.cues) == 436
    assert original.cues == TRACK.cues
    overlaps = [(a.index, b.index) for a, b in zip(original.cues, original.cues[1:]) if a.end > b.start]
    assert overlaps == [(231, 232)]
    report = compiled.report
    for raw, cue in zip(report["narration"]["cues"], original.cues):
        assert (raw["index"], raw["start"], raw["end"]) == (cue.index, cue.start, cue.end)
    assert compiled.duration == DURATION
    assert len(compiled.composition.audio) == 1
    assert compiled.composition.audio[0].start == 0
    assert all(a[2] == b[1] for a, b in pairwise(CHAPTERS))
    assert CHAPTERS[0][1] == 0 and CHAPTERS[-1][2] == DURATION


def test_geometry_dimensions_and_actual_pile_population():
    g = geometry()
    assert g["spire"].dataset.bounds[5] == pytest.approx(828)
    raft = g["raft"].dataset
    assert raft.bounds[5] - raft.bounds[4] == pytest.approx(3.7, abs=1e-5)
    piles = g["piles"].dataset.connectivity()
    assert len(np.unique(piles.cell_data["RegionId"])) == 192
    # Capped section uses the closed soil surface, not overlapping raft lobes.
    assert g["soil"].dataset.triangulate().is_manifold
    assert all(np.isfinite(mesh.dataset.points).all() for mesh in g.values())


def test_all_authored_motion_stops_before_tail_and_random_seek(compiled):
    entries = [e for e in compiled.composition.entries if isinstance(e.component, ArchChamp)]
    for entry in entries:
        clip = entry.component
        for action in clip.script.actions:
            assert entry.start + action.at + action.duration <= MOTION_END + 1e-6
        times = [0, clip.duration * 0.75, clip.duration * 0.25, clip.duration, clip.duration * 0.25]
        states = [clip.state_at(t) for t in times]
        assert states[2] == states[4]
    final = [e for e in entries if e.start == CHAPTERS[-1][1]]
    for e in final:
        a = e.component.state_at(MOTION_END - e.start)
        b = e.component.state_at(DURATION - e.start)
        assert a["parts"] == b["parts"] and a["camera"] == b["camera"]
    assert compiled.report["diagnostics"] == []
