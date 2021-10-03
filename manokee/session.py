import os
import xml.etree.ElementTree as ET
from itertools import chain
from pathlib import Path
from typing import Optional, Iterable, List, Tuple

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
            self._time_signature: int = int(
                configuration_from_file.get("time-signature", "4")
            )
            self.metronome_enabled: bool = (
                configuration_from_file.get("metronome", "0") == "1"
            )
            self.metronome_fader: Fader = Fader(
                float(configuration_from_file.get("metronome-vol", "-12")),
                float(configuration_from_file.get("metronome-pan", "0")),
            )
            marks_el = et.getroot().find("marks")
            if marks_el is not None:
                self.marks = {
                    element.attrib["name"]: Mark.from_str(element.attrib["position"])
                    for element in marks_el.findall("mark")
                }
            else:
                self.marks = {}
            track_groups_el = et.getroot().find("track-groups")
            if track_groups_el is not None:
                self.track_groups: List[TrackGroup] = [
                    TrackGroup.from_xml(
                        session=self,
                        frame_rate=frame_rate,
                        element=track_group_el,
                    )
                    for track_group_el in track_groups_el.findall("track-group")
                ]
            else:
                self.track_groups = [
                    TrackGroup(
                        name="", session=self, tracks=[], timing=FixedBpmTiming(120)
                    )
                ]
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
            self.session_format_version = "unstable"
            self.modified_with = manokee.__version__
            self._time_signature = 4
            self.metronome_enabled = False
            self.metronome_fader = Fader(-12, 0)
            self.marks = {}
            self.track_groups = [
                TrackGroup(name="", session=self, tracks=[], timing=FixedBpmTiming(120))
            ]
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
            "session", attrib={"format-name": "manokee", "format-version": "unstable"}
        )

        ET.SubElement(
            root, "program-version", attrib={"modified-with": manokee.__version__}
        )

        configuration = ET.SubElement(root, "configuration")
        ET.SubElement(
            configuration,
            "setting",
            name="time-signature",
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
            name="metronome-vol",
            value=f"{self.metronome_fader.vol_dB:.2f}",
        )
        ET.SubElement(
            configuration,
            "setting",
            name="metronome-pan",
            value=f"{self.metronome_fader.pan:.2f}",
        )

        marks = ET.SubElement(root, "marks")
        for key, mark in self.marks.items():
            ET.SubElement(marks, "mark", name=key, position=str(mark))

        track_groups_el = ET.SubElement(root, "track-groups")
        for track_group in self.track_groups:
            track_group_el = ET.SubElement(
                track_groups_el, "track-group", attrib={"name": track_group.name}
            )
            timing_el = ET.SubElement(track_group_el, "timing")
            timing = track_group.timing
            if isinstance(timing, FixedBpmTiming):
                ET.SubElement(
                    timing_el,
                    "fixed-bpm-timing",
                    attrib={"beats-per-minute": f"{timing.bpm:.2f}"},
                )
            elif isinstance(timing, AudacityTiming):
                ET.SubElement(
                    timing_el,
                    "audacity-timing",
                    attrib={
                        "audacity-project": timing.audacity_project.aup_file_path,
                        "beats-in-audacity-beat": str(timing.beats_in_audacity_beat),
                    },
                )
            else:
                raise TypeError("Unknown timing type")
            tracks_el = ET.SubElement(track_group_el, "tracks")
            for track in track_group.tracks:
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
                track_el = ET.SubElement(tracks_el, "track", attrib=attrib)
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

    @property
    def main_track_group(self) -> Optional[TrackGroup]:
        return self.track_group_by_name("")

    def track_group_by_name(self, name: str) -> TrackGroup:
        for group in self.track_groups:
            if group.name == name:
                return group
        raise KeyError(f"Track group with name '{name}' does not exist")

    def _track_name_to_group_and_index(self, name: str) -> Tuple[TrackGroup, int]:
        for group in self.track_groups:
            for i, track in enumerate(group.tracks):
                if track.name == name:
                    return group, i
        raise KeyError(f"Track with name '{name}' does not exist")

    def remove_track(self, name: str):
        try:
            group, i = self._track_name_to_group_and_index(name)
        except KeyError:
            return
        del group.tracks[i]
        self._notify_observers()

    def move_track_up(self, name: str):
        try:
            group, i = self._track_name_to_group_and_index(name)
        except KeyError:
            return
        if i == 0:
            return  # can't move the track up
        tracks = group.tracks
        tracks[i - 1], tracks[i] = (tracks[i], tracks[i - 1])
        self._notify_observers()

    def move_track_down(self, name: str):
        try:
            group, i = self._track_name_to_group_and_index(name)
        except KeyError:
            return
        tracks = group.tracks
        if i == len(tracks) - 1:
            return  # can't move the track down
        tracks[i + 1], tracks[i] = (tracks[i], tracks[i + 1])
        self._notify_observers()

    async def add_track(self, name: str, frame_rate: float):
        track = Track.empty(session=self, name=name, frame_rate=frame_rate)
        self.main_track_group.tracks.append(track)
        await track.load()
        self._notify_observers()

    @property
    def tracks(self) -> Iterable[Track]:
        return chain.from_iterable(group.tracks for group in self.track_groups)

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

        track_group = self.track_group_by_name(track_group_name)
        return list(
            chain(
                track_playspec_entries(
                    (track for track in track_group.tracks if audibility[track]),
                    reviser.audio_substitutes,
                ),
                metronome_playspec_entries(self, track_group.create_metronome()),
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
                "bpm": self.main_track_group.timing.bpm,
                "time_sig": self._time_signature,
                "metronome": "1" if self.metronome_enabled else "0",
                "metronome_vol": str(self.metronome_fader.vol_dB),
                "metronome_pan": str(self.metronome_fader.pan),
            },
            "marks": {name: str(mark) for name, mark in self.marks.items()},
            "tracks": [track.to_js() for track in self.tracks],
            "track_groups": [
                {
                    "name": group.name,
                    "average_bpm": 60 / group.timing.average_beat_length,
                }
                for group in self.track_groups
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
