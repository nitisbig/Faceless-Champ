from facelesschamp_kit.templates import narrated


def build(ctx):
    return narrated(
        ctx,
        audio="voiceover",
        subtitles="word_cues",
        markers={"hook": 1, "comparison": 2, "finish": 3},
    )
