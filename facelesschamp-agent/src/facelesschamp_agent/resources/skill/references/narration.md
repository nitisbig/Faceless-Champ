# Narration and source timing

Declare local audio and optional SRT paths in brief.narration. Preserve original cue
indices and timestamps, including accepted tiny overlaps through the explicit
overlap_tolerance setting. Never retime cues to make an animation fit.

`AgentProject.new_video(ctx)` attaches the master once at source zero. Audio without
subtitles is supported using explicit scene times. Read cues with the core public
SubtitleTrack API; Segment.cue_time maps source cues to segment-local times.

If the last cue exceeds the audio length, `fc-agent prepare` creates a checksum-tracked
WAV with a silent tail under `.fc-agent/derived/`. It leaves the source unchanged.
The brief and final visual segment must cover that tail. Normal build and validation
will request preparation if the derived copy is missing or corrupt.

Audio generation, forced alignment, and transcription are outside this package.
Without supplied audio, deliver the visual draft and a narration script. Do not claim
a narrated final. Required missing images should appear as explicit ImageCard auto
placeholders with matching geometry, and the result remains a draft.

Unchanged master audio can be checked using waveform correlation against the encoded
output. Silence, very short clips, mixes, fades, or other transformations may leave
alignment unverified. Read the actual report rather than treating an audio stream's
presence as proof that it is aligned.
