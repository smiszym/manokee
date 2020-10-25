from amio import AudioClip
import manokee.session
import numpy as np


metronome_bar_clip_mono = AudioClip.from_soundfile("res/metbar.flac")
metronome_beat_clip_mono = AudioClip.from_soundfile("res/metbeat.flac")

metronome_bar_clip = AudioClip.stereo_clip_from_mono_clips(
    metronome_bar_clip_mono, metronome_bar_clip_mono
)
metronome_beat_clip = AudioClip.stereo_clip_from_mono_clips(
    metronome_beat_clip_mono, metronome_beat_clip_mono
)


class Metronome:
    def __init__(self, session: "manokee.session.Session"):
        self._session = session
        self._needs_clip_recreation = True
        self._audio_clip = None
        self._repeat_interval = 0

    @property
    def needs_clip_recreation(self) -> bool:
        return self._needs_clip_recreation

    @needs_clip_recreation.setter
    def needs_clip_recreation(self, value: bool):
        if value == False:
            raise ValueError("Not allowed to set it externally to False")
        self._needs_clip_recreation = value

    @property
    def audio_clip(self) -> AudioClip:
        if self._needs_clip_recreation:
            self.create_audio_clip()
        return self._audio_clip

    def create_audio_clip(self):
        frame_rate = self._session.frame_rate
        beat_length_seconds = 60 / self._session.bpm
        bar_length_seconds = beat_length_seconds * self._session.time_signature
        self._repeat_interval = int(bar_length_seconds * frame_rate)
        self._audio_clip = AudioClip(np.zeros((self._repeat_interval, 2)), frame_rate)
        self._audio_clip.overwrite(metronome_bar_clip, 0)
        for i in range(1, self._session.time_signature):
            self._audio_clip.overwrite(
                metronome_beat_clip, int(i * beat_length_seconds * frame_rate)
            )
