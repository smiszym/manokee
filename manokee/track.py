from amio import AudioClip, Fader
import manokee.audacity.project as audacity_project
import manokee.session
from manokee.timing.timing import Timing
from manokee.timing.audacity_timing import AudacityTiming
import os
from typing import Callable, Optional
import xml.etree.ElementTree as ET


class Track:
    def __init__(self, session: 'manokee.session.Session', frame_rate: float,
            element: ET.Element = None, name: str = None):
        self._session = session
        if element is not None:
            assert name is None
            self._name = element.attrib['name']
            self._is_rec = element.attrib['rec'] != "0"
            self._is_mute = element.attrib['mute'] != "0"
            self._is_solo = element.attrib['solo'] != "0"
            self._rec_source = element.attrib['rec-source']
            self._source = element.attrib.get('source', 'internal')
            self._fader = Fader(
                float(element.attrib['vol']), float(element.attrib['pan']))
            self._beats_in_audacity_beat = int(
                element.attrib.get('beats-in-audacity-beat', '1'))
            self._audacity_project = (
                audacity_project.parse(element.attrib.get('audacity-project'))
                if self.is_audacity_project
                else None)
        else:
            self._name = name if name is not None else "track"
            self._is_rec = False
            self._is_mute = False
            self._is_solo = False
            self._rec_source = 'L'
            self._source = 'internal'
            self._fader = Fader()
            self._beats_in_audacity_beat = 1
            self._audacity_project = None
        self._on_modify: Optional[Callable[[], None]] = None
        self.requires_audio_save = False
        if self.is_audacity_project:
            self._audio = self.audacity_project.as_audio_clip()
            self._audio.writeable = False
        else:
            if self.filename is not None:
                try:
                    self._audio = AudioClip.from_soundfile(self.filename)
                    self._audio.writeable = False
                except FileNotFoundError:
                    self._audio = AudioClip.zeros(1, 1, frame_rate)
            else:
                self._audio = AudioClip.zeros(1, 1, frame_rate)

    @property
    def on_modify(self) -> Optional[Callable[[], None]]:
        return self._on_modify

    @on_modify.setter
    def on_modify(self, callback: Callable[[], None]):
        self._on_modify = callback

    def notify_modified(self):
        if self._on_modify is not None:
            self._on_modify()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self.notify_modified()

    @property
    def filename(self):
        if self._session.session_file_path is None:
            return None
        return os.path.join(
            os.path.dirname(self._session.session_file_path), self.name + ".flac")

    def get_audio_clip(self):
        return self._audio

    @property
    def is_rec(self) -> bool:
        return self._is_rec

    @is_rec.setter
    def is_rec(self, enabled: bool):
        self._is_rec = enabled
        self.notify_modified()

    @property
    def is_mute(self) -> bool:
        return self._is_mute

    @is_mute.setter
    def is_mute(self, enabled: bool):
        self._is_mute = enabled
        self.notify_modified()

    @property
    def is_solo(self) -> bool:
        return self._is_solo

    @is_solo.setter
    def is_solo(self, enabled: bool):
        self._is_solo = enabled
        self.notify_modified()

    @property
    def rec_source(self) -> str:
        return self._rec_source

    @rec_source.setter
    def rec_source(self, value: str):
        self._rec_source = value
        self.notify_modified()

    @property
    def source(self):
        return self._source

    @property
    def is_audacity_project(self) -> bool:
        return self._source == "audacity-project"

    @property
    def audacity_project(self):
        return self._audacity_project

    @property
    def beats_in_audacity_beat(self) -> int:
        return self._beats_in_audacity_beat

    @property
    def timing(self) -> Timing:
        if self.is_audacity_project:
            return AudacityTiming(self._audacity_project)
        else:
            return self._session.timing

    @property
    def fader(self) -> Fader:
        return self._fader

    def to_js(self) -> dict:
        return {
            'name': self._name,
            'is_rec': self._is_rec,
            'is_mute': self._is_mute,
            'is_solo': self._is_solo,
            'rec_source': self._rec_source,
            'vol_dB': self._fader.vol_dB,
            'pan': self._fader.pan,
            'requires_audio_save': self.requires_audio_save,
        }