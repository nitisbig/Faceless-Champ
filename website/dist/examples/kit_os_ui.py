from faceless_champ.os_ui import OSScript
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import SettingsWindow


def build(ctx):
    video = Video(ctx)
    script = (OSScript().set_value('appearance:theme', 'dark')
              .open_settings('sound').set_value('sound:volume', 35).wait(1))
    with video.segment('settings', duration=script.duration) as segment:
        segment.add(SettingsWindow(script=script))
    return video
