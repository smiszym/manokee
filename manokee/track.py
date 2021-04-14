from datetime import datetime, timedelta
import os
import xml.etree.ElementTree as ET

from amio import AudioClip, Fader

import manokee.audacity.project as audacity_project
import manokee.session
from manokee.input_recorder import InputFragment
from manokee.timing.timing import Timing
from manokee.timing.audacity_timing import AudacityTiming
from manokee.timing.interpolated_timing import InterpolatedTiming
from manokee.track_loader import track_loader
from manokee.wall_time_recorder import WallTimeEntry, WallTimeRecorder


def parse_timedelta(s: str) -> timedelta:
    try:
        t = datetime.strptime(s, "%H:%M:%S.%f")
    except ValueError:
        t = datetime.strptime(s, "%H:%M:%S")
    return timedelta(
        hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond
    )


class Track:
    def __init__(
        self,
        session: "manokee.session.Session",
        frame_rate: float,
        element: ET.Element = None,
        name: str = None,
    ):
        self._session = session
        self._loader = None
        self.percent_loaded = 100
        if element is not None:
            assert name is None
            self._name = element.attrib["name"]
            self._is_rec = element.attrib["rec"] != "0"
            self._is_mute = element.attrib["mute"] != "0"
            self._is_solo = element.attrib["solo"] != "0"
            self._rec_source = element.attrib["rec-source"]
            self._source = element.attrib.get("source", "internal")
            self._fader = Fader(
                float(element.attrib["vol"]), float(element.attrib["pan"])
            )
            self._beats_in_audacity_beat = int(
                element.attrib.get("beats-in-audacity-beat", "1")
            )
            self._audacity_project = (
                audacity_project.parse(element.attrib.get("audacity-project"))
                if self.is_audacity_project
                else None
            )
            self.wall_time_recorder = WallTimeRecorder(
                [
                    WallTimeEntry(
                        parse_timedelta(element.attrib["session-time"]),
                        datetime.fromisoformat(element.attrib["start-time"]),
                        parse_timedelta(element.attrib["duration"]),
                    )
                    for element in element.findall("wall-time")
                ]
            )
        else:
            self._name = name if name is not None else "track"
            self._is_rec = False
            self._is_mute = False
            self._is_solo = False
            self._rec_source = "L"
            self._source = "internal"
            self._fader = Fader()
            self._beats_in_audacity_beat = 1
            self._audacity_project = None
            self.wall_time_recorder = WallTimeRecorder()
        self.requires_audio_save = False
        if self.is_audacity_project:
            self._audio = self.audacity_project.as_audio_clip()
            self._audio.writeable = False
        else:
            if self.filename is not None:
                try:
                    self._audio, self._loader = track_loader(self.filename)
                    self.percent_loaded = 0
                    if self._audio is None:
                        self._audio = AudioClip.zeros(1, 1, frame_rate)
                except FileNotFoundError:
                    self._audio = AudioClip.zeros(1, 1, frame_rate)
            else:
                self._audio = AudioClip.zeros(1, 1, frame_rate)

    @property
    def is_loaded(self):
        return self._loader is None

    def continue_loading(self):
        if self.is_loaded:
            return
        try:
            self.percent_loaded = next(self._loader)
        except StopIteration:
            self.percent_loaded = 100
            self._loader = None
            self.notify_modified()

    def notify_modified(self):
        self._session._notify_observers()

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
            os.path.dirname(self._session.session_file_path), self.name + ".flac"
        )

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
            return InterpolatedTiming(
                AudacityTiming(self._audacity_project), self._beats_in_audacity_beat
            )
        else:
            return self._session.timing

    @property
    def fader(self) -> Fader:
        return self._fader

    def commit_input_fragment_if_needed(self, fragment: InputFragment):
        if not self._is_rec:
            return
        if not self.is_loaded:
            raise RuntimeError("Track not fully loaded yet")
        if fragment.starting_frame is None:
            raise RuntimeError("Invalid InputFragment")
        self._audio.writeable = True
        self._audio.overwrite(
            fragment.as_clip().channel(0 if self._rec_source == "L" else 1),
            fragment.starting_frame,
            extend_to_fit=True,
        )
        self._audio.writeable = False
        self.wall_time_recorder.add(
            timedelta(seconds=fragment.starting_frame / fragment.frame_rate),
            fragment.start_wall_time,
            timedelta(seconds=len(fragment) / fragment.frame_rate),
        )
        self.requires_audio_save = True
        self.notify_modified()

    def to_js(self) -> dict:
        return {
            "name": self._name,
            "is_rec": self._is_rec,
            "is_mute": self._is_mute,
            "is_solo": self._is_solo,
            "rec_source": self._rec_source,
            "vol_dB": self._fader.vol_dB,
            "pan": self._fader.pan,
            "requires_audio_save": self.requires_audio_save,
            "is_loaded": self.is_loaded,
            "percent_loaded": self.percent_loaded,
        }
