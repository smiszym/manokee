from amio import AudioClip, Fader, Interface, Playspec
import manokee  # __version__
import manokee.audacity.project as audacity_project
import manokee.metronome
from manokee.playspec_generator import PlayspecGenerator
from manokee.playspec_source import MetronomePlayspecSource, \
    SessionTracksPlayspecSource
from manokee.timing.audacity_timing import AudacityTiming
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.timing import Timing
import os
from typing import Callable, Optional
import xml.etree.ElementTree as ET


# ET.indent() will be available from Python 3.9; until then, I use
# the implementation from http://effbot.org/zone/element-lib.htm#prettyprint
# below.
# (see https://bugs.python.org/issue14465)
def _ET_indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _ET_indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Track:
    def __init__(self, session: 'Session', frame_rate: float,
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


class Session:
    def __init__(self, frame_rate: float,
                 session_file_path: Optional[str] = None):
        self._session_file_path: Optional[str] = None
        if session_file_path is not None and os.path.exists(session_file_path):
            if os.path.isdir(session_file_path):
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path, "session.mnk")
            else:
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path)
            et = ET.parse(self._session_file_path)
            self._session_format_name = et.getroot().attrib['format-name']
            self._session_format_version = et.getroot().attrib['format-version']
            modified_with_el = et.getroot().find('program-version')
            self._modified_with: Optional[str] = None
            if modified_with_el is not None:
                self._modified_with = modified_with_el.attrib['modified-with']
            configuration_el = et.getroot().find('configuration')
            if configuration_el is not None:
                self._configuration = {
                    element.attrib['name']: element.attrib['value']
                    for element
                    in configuration_el.findall('setting')}
            else:
                self._configuration = {}
            marks_el = et.getroot().find('marks')
            if marks_el is not None:
                self._marks = {
                    element.attrib['name']: element.attrib['position']
                    for element in marks_el.findall('mark')}
            else:
                self._marks = {}
            tracks_el = et.getroot().find('tracks')
            if tracks_el is not None:
                self._tracks = [Track(self, frame_rate, element) for element
                                in tracks_el.findall('track')]
            else:
                self._tracks = []
            for track in self._tracks:
                track.on_modify = self._onModified
        else:
            if session_file_path is None:
                self._session_file_path = None
            elif session_file_path.endswith(".mnk"):
                self._session_file_path = session_file_path
            else:
                self._session_file_path = os.path.join(
                    os.path.curdir, session_file_path, "session.mnk")
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
        self._on_modify: Optional[Callable[[], None]] = None

    def save(self):
        assert self._session_file_path is not None

        session_dir = os.path.dirname(self._session_file_path)
        try:
            os.mkdir(session_dir)
        except FileExistsError:
            # That's ok, just check if session_dir is indeed a Manokee
            # session.
            if not os.path.isdir(session_dir):
                raise FileExistsError("Session path is not a directory")
            if (len(os.listdir(session_dir)) > 0
                and not os.path.isfile(
                            os.path.join(session_dir, "session.mnk"))):
                raise FileExistsError("Directory is not a Manokee session")

        for track in self._tracks:
            if track.requires_audio_save:
                track.get_audio_clip().to_soundfile(track.filename)
                track.requires_audio_save = False

        root = ET.Element(
            'session', attrib={'format-name': 'manokee', 'format-version': '1'})

        ET.SubElement(
            root, 'program-version',
            attrib={'modified-with': manokee.__version__})

        configuration = ET.SubElement(root, 'configuration')
        for key, value in self._configuration.items():
            ET.SubElement(configuration, 'setting', name=key, value=value)

        marks = ET.SubElement(root, 'marks')
        for key, value in self._marks.items():
            ET.SubElement(marks, 'mark', name=key, position=value)

        tracks = ET.SubElement(root, 'tracks')
        for track in self._tracks:
            ET.SubElement(
                tracks, 'track',
                attrib={
                    'rec': "1" if track.is_rec else "0",
                    'rec-source': track.rec_source,
                    'mute': "1" if track.is_mute else "0",
                    'solo': "1" if track.is_solo else "0",
                    'vol': str(track.fader.vol_dB),
                    'pan': str(track.fader.pan),
                    'name': track.name,
                    })

        _ET_indent(root)
        tree = ET.ElementTree(root)
        tree.write(self._session_file_path)
        self._are_controls_modified = False

    @property
    def on_modify(self) -> Optional[Callable[[], None]]:
        return self._on_modify

    @on_modify.setter
    def on_modify(self, callback: Callable[[], None]):
        self._on_modify = callback

    @property
    def are_controls_modified(self) -> bool:
        return self._are_controls_modified

    def _onModified(self):
        self._are_controls_modified = True
        if self._on_modify is not None:
            self._on_modify()

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
        self._onModified()

    def move_track_up(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == 0:
            return  # can't move the track up
        self._tracks[i - 1], self._tracks[i] = (
            self._tracks[i], self._tracks[i - 1])
        self._onModified()

    def move_track_down(self, name: str):
        i = self._index_of_track(name)
        if i is None or i == len(self._tracks) - 1:
            return  # can't move the track down
        self._tracks[i + 1], self._tracks[i] = (
            self._tracks[i], self._tracks[i + 1])
        self._onModified()

    def add_track(self, name: str, frame_rate: float):
        track = Track(self, frame_rate, element=None, name=name)
        track.on_modify = self._onModified
        self._tracks.append(track)
        self._onModified()

    @property
    def bpm(self) -> float:
        return float(self._configuration['bpm'])

    @bpm.setter
    def bpm(self, value: float):
        self._configuration['bpm'] = str(value)
        self._onModified()

    @property
    def time_signature(self) -> int:
        return int(self._configuration['time_sig'])

    @time_signature.setter
    def time_signature(self, value: int):
        self._configuration['time_sig'] = str(value)
        self._onModified()

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

    def toggle_metronome(self):
        new_value = not (self._configuration['metronome'] == "1")
        self._configuration['metronome'] = "1" if new_value == True else "0"
        self._onModified()

    def metronome_vol_down(self):
        new_value = float(self._configuration['metronome_vol']) - 1
        self._configuration['metronome_vol'] = str(new_value)
        self._onModified()

    def metronome_vol_up(self):
        new_value = float(self._configuration['metronome_vol']) + 1
        self._configuration['metronome_vol'] = str(new_value)
        self._onModified()

    def make_playspec_from_tracks(self, amio_interface: Interface,
            metronome: 'manokee.metronome.Metronome', tracks) -> Playspec:
        playspec_generator = PlayspecGenerator(amio_interface)
        playspec_generator.add_source(SessionTracksPlayspecSource(tracks))
        playspec_generator.add_source(MetronomePlayspecSource(self, metronome))
        return playspec_generator.make_playspec()

    def to_js(self) -> dict:
        """
        Make a JSON-line representation of the session, to be sent
        to the client.
        :return: A Python dictionary with JSON-like session representation.
        """
        return {
            'name': self.name,
            'are_controls_modified': self.are_controls_modified,
            'configuration': self._configuration,
            'marks': self._marks,
            'tracks': [track.to_js() for track in self._tracks],
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
