import os
import xml.etree.ElementTree as ET
from itertools import chain
from pathlib import Path
from typing import Optional, Mapping

from amio import Playspec, Fader

import manokee  # __version__
import manokee.revising
from manokee.mark import Mark
from manokee.observable import ObservableMixin
from manokee.playspec_generators import (
    track_playspec_entries,
    metronome_playspec_entries,
)
from manokee.session_history import SessionHistory
from manokee.track import Track
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.timing import Timing
from manokee.track_group import TrackGroup
from manokee.utils import ET_indent


class Session(ObservableMixin):
    def __init__(self, frame_rate: float, session_file_path: Optional[str] = None):
        super().__init__()
        self.frame_rate = frame_rate
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
            self.session_format_name: str = et.getroot().attrib["format-name"]
            self.session_format_version: str = et.getroot().attrib["format-version"]
            modified_with_el = et.getroot().find("program-version")
            self.modified_with: Optional[str] = None
            if modified_with_el is not None:
                self.modified_with = modified_with_el.attrib["modified-with"]
            configuration_el = et.getroot().find("configuration")
            if configuration_el is not None:
                configuration_from_file = {
                    element.attrib["name"]: element.attrib["value"]
                    for element in configuration_el.findall("setting")
                }
            else:
                configuration_from_file = {}
            self._bpm: float = float(configuration_from_file.get("bpm", "120"))
            self._time_signature: int = int(
                configuration_from_file.get("time_sig", "4")
            )
            self.metronome_enabled: bool = (
                configuration_from_file.get("metronome", "0") == "1"
            )
            self.metronome_fader: Fader = Fader(
                float(configuration_from_file.get("metronome_vol", "-12")),
                float(configuration_from_file.get("metronome_pan", "0")),
            )
            marks_el = et.getroot().find("marks")
            if marks_el is not None:
                self.marks = {
                    element.attrib["name"]: Mark.from_str(element.attrib["position"])
                    for element in marks_el.findall("mark")
                }
            else:
                self.marks = {}
            tracks_el = et.getroot().find("tracks")
            if tracks_el is not None:
                self.tracks = [
                    Track.from_xml(session=self, frame_rate=frame_rate, element=element)
                    for element in tracks_el.findall("track")
                ]
            else:
                self.tracks = []
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
            self.session_format_name = "manokee"
            self.session_format_version = "1"
            self.modified_with = manokee.__version__
            self._bpm = 120
            self._time_signature = 4
            self.metronome_enabled = False
            self.metronome_fader = Fader(-12, 0)
            self.marks = {}
            self.tracks = []
        self._are_controls_modified = False

    def save(self):
        assert self._session_file_path is not None
        assert all(track.is_loaded for track in self.tracks)

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

        for track in self.tracks:
            if track.requires_audio_save:
                track.audio.to_soundfile(track.filename)
                track.requires_audio_save = False

        root = ET.Element(
            "session", attrib={"format-name": "manokee", "format-version": "1"}
        )

        ET.SubElement(
            root, "program-version", attrib={"modified-with": manokee.__version__}
        )

        configuration = ET.SubElement(root, "configuration")
        ET.SubElement(configuration, "setting", name="bpm", value=f"{self._bpm:.2f}")
        ET.SubElement(
            configuration,
            "setting",
            name="time_sig",
            value=str(self._time_signature),
        )
        ET.SubElement(
            configuration,
            "setting",
            name="metronome",
            value="1" if self.metronome_enabled else "0",
        )
        ET.SubElement(
            configuration,
            "setting",
            name="metronome_vol",
            value=f"{self.metronome_fader.vol_dB:.2f}",
        )
        ET.SubElement(
            configuration,
            "setting",
            name="metronome_pan",
            value=f"{self.metronome_fader.pan:.2f}",
        )

        marks = ET.SubElement(root, "marks")
        for key, mark in self.marks.items():
            ET.SubElement(marks, "mark", name=key, position=str(mark))

        tracks = ET.SubElement(root, "tracks")
        for track in self.tracks:
            attrib = {
                "rec": "1" if track.is_rec else "0",
                "rec-source": track.rec_source,
                "mute": "1" if track.is_mute else "0",
                "solo": "1" if track.is_solo else "0",
                "vol": f"{track.fader.vol_dB:.2f}",
                "pan": f"{track.fader.pan:.2f}",
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

        ET_indent(root)
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

    def mark_position_seconds(self, name: str, timing: Timing) -> Optional[float]:
        mark = self.marks[name]
        if mark is None:
            return None
        return timing.beat_to_seconds(mark.beat)

    def set_mark_at_beat(self, name, beat):
        self.marks[name] = Mark(beat=beat)

    def track_for_name(self, name: str) -> Optional[Track]:
        for track in self.tracks:
            if track.name == name:
                return track
        return None

    def _index_of_track(self, name: str) -> Optional[int]:
        for i, track in enumerate(self.tracks):
            if track.name == name:
                return i
        return None

    def remove_track(self, name: str):
        i = self._index_of_track(name)
        if i is not None:
            del self.tracks[i]
        self._notify_observers()

    def move_track_up(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == 0:
            return  # can't move the track up
        self.tracks[i - 1], self.tracks[i] = (self.tracks[i], self.tracks[i - 1])
        self._notify_observers()

    def move_track_down(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == len(self.tracks) - 1:
            return  # can't move the track down
        self.tracks[i + 1], self.tracks[i] = (self.tracks[i], self.tracks[i + 1])
        self._notify_observers()

    async def add_track(self, name: str, frame_rate: float):
        track = Track.empty(session=self, name=name, frame_rate=frame_rate)
        self.tracks.append(track)
        await track.load()
        self._notify_observers()

    @property
    def track_groups(self) -> Mapping[str, TrackGroup]:
        audacity_groups = [
            track.name for track in self.tracks if track.is_audacity_project
        ]
        return {
            name: TrackGroup(name=name, session=self) for name in [""] + audacity_groups
        }

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, value: float):
        self._bpm = value
        self._notify_observers()

    @property
    def time_signature(self) -> int:
        return self._time_signature

    @time_signature.setter
    def time_signature(self, value: int):
        self._time_signature = value
        self._notify_observers()

    def beat_to_bar(self, beat: float) -> float:
        return beat / self.time_signature

    def bar_to_beat(self, bar: float) -> float:
        return bar * self.time_signature

    @property
    def timing(self) -> Timing:
        return FixedBpmTiming(self._bpm)

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
        self.metronome_enabled = not self.metronome_enabled
        self._notify_observers()

    def metronome_vol_down(self):
        self.metronome_fader.vol_dB -= 1
        self._notify_observers()

    def metronome_vol_up(self):
        self.metronome_fader.vol_dB += 1
        self._notify_observers()

    def change_metronome_pan(self, new_pan: float) -> None:
        self.metronome_fader.pan = new_pan
        self._notify_observers()

    def make_playspec_for_track_group(
        self,
        track_group_name: str,
        is_recording: bool,
        reviser: "manokee.revising.Reviser",
    ) -> Playspec:
        # First, calculate basic audibility of tracks from solo and mute values
        is_soloed = any(track.is_solo for track in self.tracks)
        audibility = {
            track: track.is_solo if is_soloed else not track.is_mute
            for track in self.tracks
        }
        # Then, exclude tracks currently being recorded
        if is_recording:
            for track in self.tracks:
                if track.is_rec:
                    audibility[track] = False
        return list(
            chain(
                track_playspec_entries(
                    (
                        track
                        for track in self.track_groups[track_group_name].tracks
                        if audibility[track]
                    ),
                    reviser.audio_substitutes,
                ),
                metronome_playspec_entries(
                    self, self.track_groups[track_group_name].create_metronome()
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
            "configuration": {
                "bpm": self._bpm,
                "time_sig": self._time_signature,
                "metronome": "1" if self.metronome_enabled else "0",
                "metronome_vol": str(self.metronome_fader.vol_dB),
                "metronome_pan": str(self.metronome_fader.pan),
            },
            "marks": {name: str(mark) for name, mark in self.marks.items()},
            "tracks": [track.to_js() for track in self.tracks],
            "track_groups": [
                {
                    "name": name,
                    "average_bpm": group.average_bpm,
                }
                for name, group in self.track_groups.items()
            ],
            "history": self.history.to_js(),
        }

    @property
    def session_directory(self) -> Optional[Path]:
        if self._session_file_path is None:
            return None
        return Path(self._session_file_path).parent

    def files_in_session_directory(self) -> Optional[set[Path]]:
        session_directory = self.session_directory
        if session_directory is None:
            return None
        all_files: set[Path] = set()
        for root, dirs, files in os.walk(session_directory):
            try:
                dirs.remove(".git")
            except ValueError:
                pass
            all_files.update(Path(root) / file for file in files)
        return all_files

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
