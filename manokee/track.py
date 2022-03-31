import asyncio
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from amio import AudioClip, Fader
import soundfile as sf

import manokee.audacity.project as aup
import manokee.session
from manokee.input_recorder import InputFragment
from manokee.timing.timing import Timing
from manokee.timing.audacity_timing import AudacityTiming
from manokee.wall_time_recorder import WallTimeEntry, WallTimeRecorder


def parse_timedelta(s: str) -> timedelta:
    try:
        t = datetime.strptime(s, "%H:%M:%S.%f")
    except ValueError:
        t = datetime.strptime(s, "%H:%M:%S")
    return timedelta(
        hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond
    )


@dataclass(eq=False)
class Track:
    session: "manokee.session.Session"

    name: str
    rec_source: str
    fader: Fader
    frame_rate: float

    percent_loaded: Optional[float]

    audio: AudioClip
    wall_time_recorder: WallTimeRecorder

    average_bpm: Optional[float] = None
    audacity_project: Optional[aup.AudacityProject] = None
    aup_file_path: Optional[str] = None
    audacity_track: Optional[str] = None
    beats_in_audacity_beat: int = 1
    source: str = "internal"
    requires_audio_save: bool = False

    is_rec: bool = False
    is_mute: bool = False
    is_solo: bool = False

    @classmethod
    def empty(cls, session, name: str, frame_rate: float):
        return cls(
            session=session,
            name=name if name is not None else "track",
            rec_source="L",
            fader=Fader(),
            frame_rate=frame_rate,
            percent_loaded=0,
            audio=AudioClip.zeros(1, 1, frame_rate),
            wall_time_recorder=WallTimeRecorder(),
        )

    @classmethod
    def from_xml(cls, session, frame_rate: float, element: ET.Element):
        aup_file_path = element.attrib.get("audacity-project")
        if element.attrib.get("source", "internal") == "audacity-project":
            percent_loaded = None
            audacity_project = aup.parse(session.relative_path(aup_file_path))
        else:
            percent_loaded = 0
            audacity_project = None

        result = cls(
            session=session,
            name=element.attrib["name"],
            is_rec=element.attrib["rec"] != "0",
            is_mute=element.attrib["mute"] != "0",
            is_solo=element.attrib["solo"] != "0",
            rec_source=element.attrib["rec-source"],
            fader=Fader(float(element.attrib["vol"]), float(element.attrib["pan"])),
            frame_rate=frame_rate,
            percent_loaded=percent_loaded,
            audio=AudioClip.zeros(1, 1, frame_rate),
            wall_time_recorder=WallTimeRecorder(
                [
                    WallTimeEntry(
                        parse_timedelta(element.attrib["session-time"]),
                        datetime.fromisoformat(element.attrib["start-time"]),
                        parse_timedelta(element.attrib["duration"]),
                    )
                    for element in element.findall("wall-time")
                ]
            ),
            audacity_project=audacity_project,
            aup_file_path=aup_file_path,
            audacity_track=element.attrib.get("audacity-track"),
            beats_in_audacity_beat=int(
                element.attrib.get("beats-in-audacity-beat", "1")
            ),
            source=element.attrib.get("source", "internal"),
        )
        if result.is_audacity_project:
            result.audio = result.audacity_project.as_audio_clip(  # type: ignore
                track=result.audacity_track
            )
            result.audio.writeable = False

        result._calculate_average_bpm()

        return result

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
            self.audio = AudioClip.zeros(f.frames, f.channels, f.samplerate)
            self.audio.writeable = True

            read_so_far = 0
            blocksize = 30 * f.samplerate  # load in 30-second chunks
            for block in f.blocks(blocksize=blocksize):
                self.audio.overwrite(AudioClip(block, f.samplerate), read_so_far)
                read_so_far += blocksize
                self.percent_loaded = 100 * read_so_far / f.frames
                await asyncio.sleep(0)

            f.close()
            self.audio.writeable = False
            self.percent_loaded = None

    @property
    def filename(self):
        return self.session.relative_path(self.name + ".flac")

    @property
    def is_audacity_project(self) -> bool:
        return self.source == "audacity-project"

    def commit_input_fragment_if_needed(self, fragment: InputFragment):
        if not self.is_rec:
            return
        if not self.is_loaded:
            raise RuntimeError("Track not fully loaded yet")
        if fragment.starting_frame is None:
            raise RuntimeError("Invalid InputFragment")
        self.audio.writeable = True
        self.audio.overwrite(
            fragment.as_clip().channel(0 if self.rec_source == "L" else 1),
            fragment.starting_frame,
            extend_to_fit=True,
        )
        self.audio.writeable = False
        self.wall_time_recorder.add(
            timedelta(seconds=fragment.starting_frame / fragment.frame_rate),
            fragment.start_wall_time,
            timedelta(seconds=len(fragment) / fragment.frame_rate),
        )
        self.requires_audio_save = True

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
            "source": self.source,
        }

    def _calculate_average_bpm(self) -> None:
        if self.is_audacity_project:
            self.average_bpm = (
                60.0
                / AudacityTiming(
                    project=self.audacity_project,  # type: ignore
                    aup_file_path=self.aup_file_path,  # type: ignore
                ).average_beat_length
            )
        else:
            self.average_bpm = None
