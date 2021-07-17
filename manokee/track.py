import asyncio
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from amio import AudioClip, Fader
import soundfile as sf

import manokee.audacity.project as audacity_project
import manokee.session
from manokee.input_recorder import InputFragment
from manokee.timing.timing import Timing
from manokee.timing.audacity_timing import AudacityTiming
from manokee.timing.interpolated_timing import InterpolatedTiming
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
        self.percent_loaded = None
        self.frame_rate = frame_rate
        if element is not None:
            assert name is None
            self.name = element.attrib["name"]
            self.is_rec = element.attrib["rec"] != "0"
            self.is_mute = element.attrib["mute"] != "0"
            self.is_solo = element.attrib["solo"] != "0"
            self.rec_source = element.attrib["rec-source"]
            self._source = element.attrib.get("source", "internal")
            self.fader = Fader(
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
            self.name = name if name is not None else "track"
            self.is_rec = False
            self.is_mute = False
            self.is_solo = False
            self.rec_source = "L"
            self._source = "internal"
            self.fader = Fader()
            self._beats_in_audacity_beat = 1
            self._audacity_project = None
            self.wall_time_recorder = WallTimeRecorder()
        self.requires_audio_save = False
        if self.is_audacity_project:
            self._audio = self.audacity_project.as_audio_clip()
            self._audio.writeable = False
            self.average_bpm: Optional[float] = self._calculate_average_bpm()
        else:
            self._audio = AudioClip.zeros(1, 1, self.frame_rate)
            self.percent_loaded = 0
            self.average_bpm = None

    @property
    def is_loaded(self):
        return self.percent_loaded is None

    async def load(self):
        if self.is_loaded:
            return

        try:
            if not self.filename or os.path.getsize(self.filename) == 0:
                raise FileNotFoundError
            f = sf.SoundFile(self.filename)
        except FileNotFoundError:
            self.percent_loaded = None
        else:
            self._audio = AudioClip.zeros(f.frames, f.channels, f.samplerate)
            self._audio.writeable = True

            read_so_far = 0
            blocksize = 30 * f.samplerate  # load in 30-second chunks
            for block in f.blocks(blocksize=blocksize):
                self._audio.overwrite(AudioClip(block, f.samplerate), read_so_far)
                read_so_far += blocksize
                self.percent_loaded = 100 * read_so_far / f.frames
                await asyncio.sleep(0)

            f.close()
            self._audio.writeable = False
            self.percent_loaded = None
            self.notify_modified()

    def notify_modified(self):
        self._session._notify_observers()

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

    def commit_input_fragment_if_needed(self, fragment: InputFragment):
        if not self.is_rec:
            return
        if not self.is_loaded:
            raise RuntimeError("Track not fully loaded yet")
        if fragment.starting_frame is None:
            raise RuntimeError("Invalid InputFragment")
        self._audio.writeable = True
        self._audio.overwrite(
            fragment.as_clip().channel(0 if self.rec_source == "L" else 1),
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
            "name": self.name,
            "is_rec": self.is_rec,
            "is_mute": self.is_mute,
            "is_solo": self.is_solo,
            "rec_source": self.rec_source,
            "vol_dB": self.fader.vol_dB,
            "pan": self.fader.pan,
            "requires_audio_save": self.requires_audio_save,
            "is_loaded": self.is_loaded,
            "percent_loaded": self.percent_loaded,
        }

    def _calculate_average_bpm(self) -> float:
        return (
            60.0
            / AudacityTiming(self._audacity_project).average_beat_length
            * self._beats_in_audacity_beat
        )
