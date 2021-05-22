from amio import AudioClip


metronome_bar_clip = AudioClip.from_soundfile("res/metbar.flac")
metronome_beat_clip = AudioClip.from_soundfile("res/metbeat.flac")


# TODO: Support variable-bpm metronome
class Metronome:
    def __init__(self, *, bpm: float, time_signature: int, frame_rate: float):
        beat_length_seconds = 60 / bpm
        bar_length_seconds = beat_length_seconds * time_signature
        repeat_interval = int(bar_length_seconds * frame_rate)
        self.audio_clip = AudioClip.zeros(repeat_interval, 1, frame_rate)
        self.audio_clip.overwrite(metronome_bar_clip, 0)
        for i in range(1, time_signature):
            self.audio_clip.overwrite(
                metronome_beat_clip, int(i * beat_length_seconds * frame_rate)
            )
