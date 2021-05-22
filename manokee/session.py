from amio import Interface, Playspec
from itertools import chain
import manokee  # __version__
from manokee.mark import Mark
from manokee.metronome import Metronome
from manokee.observable import ObservableMixin
from manokee.playspec_generators import (
    track_playspec_entries,
    metronome_playspec_entries,
)
import manokee.revising
from manokee.session_history import SessionHistory
from manokee.track import Track
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.interpolated_timing import InterpolatedTiming
from manokee.timing.timing import Timing
import os
from typing import Callable, Dict, Optional, List
import xml.etree.ElementTree as ET


# ET.indent() will be available from Python 3.9; until then, I use
# the implementation from http://effbot.org/zone/element-lib.htm#prettyprint
# below.
# (see https://bugs.python.org/issue14465)
def _ET_indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _ET_indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Session(ObservableMixin):
    def __init__(self, frame_rate: float, session_file_path: Optional[str] = None):
        super().__init__()
        self._frame_rate = frame_rate
        self._session_file_path: Optional[str] = None
        if session_file_path is not None and os.path.exists(session_file_path):
            if os.path.isdir(session_file_path):
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path, "session.mnk"
                )
            else:
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path
                )
            self.history = SessionHistory(os.path.dirname(self._session_file_path))
            et = ET.parse(self._session_file_path)
            self._session_format_name = et.getroot().attrib["format-name"]
            self._session_format_version = et.getroot().attrib["format-version"]
            modified_with_el = et.getroot().find("program-version")
            self._modified_with: Optional[str] = None
            if modified_with_el is not None:
                self._modified_with = modified_with_el.attrib["modified-with"]
            configuration_el = et.getroot().find("configuration")
            if configuration_el is not None:
                self._configuration = {
                    element.attrib["name"]: element.attrib["value"]
                    for element in configuration_el.findall("setting")
                }
            else:
                self._configuration = {}
            marks_el = et.getroot().find("marks")
            if marks_el is not None:
                self._marks = {
                    element.attrib["name"]: Mark.from_str(element.attrib["position"])
                    for element in marks_el.findall("mark")
                }
            else:
                self._marks = {}
            tracks_el = et.getroot().find("tracks")
            if tracks_el is not None:
                self._tracks = [
                    Track(self, frame_rate, element)
                    for element in tracks_el.findall("track")
                ]
            else:
                self._tracks = []
        else:
            self.history = SessionHistory(None)
            if session_file_path is None:
                self._session_file_path = None
            elif session_file_path.endswith(".mnk"):
                self._session_file_path = session_file_path
            else:
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path, "session.mnk"
                )
            self._session_format_name = "manokee"
            self._session_format_version = "1"
            self._modified_with = manokee.__version__
            self._configuration = {
                "tape_length": "10",
                "bpm": "120",
                "time_sig": "4",
                "intro_len": "-1",
                "met_intro_only": "0",
                "metronome": "0",
                "metronome_vol": "-12.0",
                "metronome_pan": "0",
            }
            self._marks = {}
            self._tracks = []
        self._are_controls_modified = False

    def save(self):
        assert self._session_file_path is not None
        assert all(track.is_loaded for track in self._tracks)

        session_dir = os.path.dirname(self._session_file_path)
        try:
            os.mkdir(session_dir)
        except FileExistsError:
            # That's ok, just check if session_dir is indeed a Manokee
            # session.
            if not os.path.isdir(session_dir):
                raise FileExistsError("Session path is not a directory")
            if len(os.listdir(session_dir)) > 0 and not os.path.isfile(
                os.path.join(session_dir, "session.mnk")
            ):
                raise FileExistsError("Directory is not a Manokee session")

        for track in self._tracks:
            if track.requires_audio_save:
                track.get_audio_clip().to_soundfile(track.filename)
                track.requires_audio_save = False

        root = ET.Element(
            "session", attrib={"format-name": "manokee", "format-version": "1"}
        )

        ET.SubElement(
            root, "program-version", attrib={"modified-with": manokee.__version__}
        )

        configuration = ET.SubElement(root, "configuration")
        for key, value in self._configuration.items():
            ET.SubElement(configuration, "setting", name=key, value=value)

        marks = ET.SubElement(root, "marks")
        for key, mark in self._marks.items():
            ET.SubElement(marks, "mark", name=key, position=str(mark))

        tracks = ET.SubElement(root, "tracks")
        for track in self._tracks:
            attrib = {
                "rec": "1" if track.is_rec else "0",
                "rec-source": track.rec_source,
                "mute": "1" if track.is_mute else "0",
                "solo": "1" if track.is_solo else "0",
                "vol": str(track.fader.vol_dB),
                "pan": str(track.fader.pan),
                "name": track.name,
                "source": track.source,
            }
            if track.is_audacity_project:
                attrib["audacity-project"] = track.audacity_project.aup_file_path
                attrib["beats-in-audacity-beat"] = str(track.beats_in_audacity_beat)
            track_el = ET.SubElement(tracks, "track", attrib=attrib)
            for entry in track.wall_time_recorder.entries:
                ET.SubElement(
                    track_el,
                    "wall-time",
                    attrib={
                        "session-time": str(entry.session_time),
                        "start-time": str(entry.start_time),
                        "duration": str(entry.duration),
                    },
                )

        _ET_indent(root)
        tree = ET.ElementTree(root)
        tree.write(self._session_file_path)
        self._are_controls_modified = False

    @property
    def are_controls_modified(self) -> bool:
        return self._are_controls_modified

    @property
    def session_file_path(self):
        return self._session_file_path

    @session_file_path.setter
    def session_file_path(self, value):
        # TODO: Keep path under which Session was previously saved
        # (can be None) and do this kind of checks in save()
        if Session.exists_on_disk(self._session_file_path):
            raise NotImplementedError
        if not Session.is_suitable_for_overwrite(value):
            raise NotImplementedError
        self._session_file_path = value

    @property
    def name(self) -> Optional[str]:
        # TODO: Store the session name inside the session file
        if self._session_file_path is None:
            return None
        return os.path.basename(os.path.dirname(self._session_file_path))

    @property
    def session_format_name(self) -> str:
        return self._session_format_name

    @property
    def session_format_version(self) -> str:
        return self._session_format_version

    @property
    def modified_with(self) -> Optional[str]:
        return self._modified_with

    @property
    def configuration(self) -> dict:
        return self._configuration

    @property
    def frame_rate(self) -> float:
        return self._frame_rate

    def mark_position_seconds(self, name: str, timing: Timing) -> Optional[float]:
        mark = self._marks[name]
        if mark is None:
            return None
        return timing.beat_to_seconds(mark.beat)

    def set_mark_at_beat(self, name, beat):
        self._marks[name] = Mark(beat=beat)

    @property
    def marks(self) -> dict:
        return self._marks

    @property
    def tracks(self) -> list:
        return self._tracks

    def track_for_name(self, name: str) -> Optional[Track]:
        for track in self._tracks:
            if track.name == name:
                return track
        return None

    def _index_of_track(self, name: str) -> Optional[int]:
        for i, track in enumerate(self._tracks):
            if track.name == name:
                return i
        return None

    def remove_track(self, name: str):
        i = self._index_of_track(name)
        if i is not None:
            del self._tracks[i]
        self._notify_observers()

    def move_track_up(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == 0:
            return  # can't move the track up
        self._tracks[i - 1], self._tracks[i] = (self._tracks[i], self._tracks[i - 1])
        self._notify_observers()

    def move_track_down(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == len(self._tracks) - 1:
            return  # can't move the track down
        self._tracks[i + 1], self._tracks[i] = (self._tracks[i], self._tracks[i + 1])
        self._notify_observers()

    def add_track(self, name: str, frame_rate: float):
        track = Track(self, frame_rate, element=None, name=name)
        self._tracks.append(track)
        self._notify_observers()

    @property
    def track_group_names(self) -> List[str]:
        audacity_groups = [
            track.name for track in self._tracks if track.is_audacity_project
        ]
        return [""] + audacity_groups

    def tracks_in_group(self, track_group_name: str):
        if track_group_name == "":
            # The main track group
            return [track for track in self._tracks if not track.is_audacity_project]
        else:
            # Audacity track group
            return [self.track_for_name(track_group_name)]

    def create_metronome_for_track_group(
        self, track_group_name: str
    ) -> Optional["Metronome"]:
        if track_group_name == "":
            return Metronome(
                bpm=self.bpm,
                time_signature=self.time_signature,
                frame_rate=self.frame_rate,
            )
        else:
            return None

    @property
    def bpm(self) -> float:
        return float(self._configuration["bpm"])

    @bpm.setter
    def bpm(self, value: float):
        self._configuration["bpm"] = str(value)
        self._notify_observers()

    @property
    def time_signature(self) -> int:
        return int(self._configuration["time_sig"])

    @time_signature.setter
    def time_signature(self, value: int):
        self._configuration["time_sig"] = str(value)
        self._notify_observers()

    def beat_to_bar(self, beat: float) -> float:
        return beat / self.time_signature

    def bar_to_beat(self, bar: float) -> float:
        return bar * self.time_signature

    @property
    def timing(self) -> Timing:
        return FixedBpmTiming(self.bpm)

    @property
    def track_timings(self) -> set:
        return {track.timing for track in self.tracks}

    def group_timing(self, track_group_name: str) -> Timing:
        if track_group_name == "":
            return self.timing
        else:
            track = self.track_for_name(track_group_name)
            if track is None:
                raise ValueError(f"No such track: {track_group_name}")
            return track.timing

    def toggle_metronome(self):
        new_value = not (self._configuration["metronome"] == "1")
        self._configuration["metronome"] = "1" if new_value == True else "0"
        self._notify_observers()

    def metronome_vol_down(self):
        new_value = float(self._configuration["metronome_vol"]) - 1
        self._configuration["metronome_vol"] = str(new_value)
        self._notify_observers()

    def metronome_vol_up(self):
        new_value = float(self._configuration["metronome_vol"]) + 1
        self._configuration["metronome_vol"] = str(new_value)
        self._notify_observers()

    def change_metronome_pan(self, new_pan: float) -> None:
        self._configuration["metronome_pan"] = str(new_pan)
        self._notify_observers()

    def make_playspec_for_track_group(
        self,
        track_group_name: str,
        is_recording: bool,
        reviser: "manokee.revising.Reviser",
    ) -> Playspec:
        # First, calculate basic audibility of tracks from solo and mute values
        is_soloed = any(track.is_solo for track in self._tracks)
        audibility = {
            track: track.is_solo if is_soloed else not track.is_mute
            for track in self._tracks
        }
        # Then, exclude tracks currently being recorded
        if is_recording:
            for track in self._tracks:
                if track.is_rec:
                    audibility[track] = False
        return list(
            chain(
                track_playspec_entries(
                    (
                        track
                        for track in self.tracks_in_group(track_group_name)
                        if audibility[track]
                    ),
                    reviser.audio_substitutes,
                ),
                metronome_playspec_entries(
                    self, self.create_metronome_for_track_group(track_group_name)
                ),
            )
        )

    def to_js(self) -> dict:
        """
        Make a JSON-line representation of the session, to be sent
        to the client.
        :return: A Python dictionary with JSON-like session representation.
        """
        return {
            "name": self.name,
            "are_controls_modified": self.are_controls_modified,
            "configuration": self._configuration,
            "marks": {name: str(mark) for name, mark in self._marks.items()},
            "tracks": [track.to_js() for track in self._tracks],
            "track_group_names": self.track_group_names,
            "history": self.history.to_js(),
        }

    @staticmethod
    def is_suitable_for_overwrite(session_file_path) -> bool:
        if session_file_path is None:
            return True
        session_dir = os.path.dirname(session_file_path)
        if not os.path.exists(session_dir):
            return True
        if os.path.isdir(session_dir) and len(os.listdir(session_dir)) == 0:
            return True
        return False

    @staticmethod
    def exists_on_disk(session_file_path) -> bool:
        if session_file_path is None:
            return False
        return os.path.isfile(session_file_path)
