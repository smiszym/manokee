from amio import AudioClip, Fader, Playspec
import manokee
import manokee.audacity.project as audacity_project
from manokee.playspec_generator import PlayspecGenerator
from manokee.playspec_source import MetronomePlayspecSource, \
    SessionTracksPlayspecSource
from manokee.timing.audacity_timing import AudacityTiming
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
import os
import xml.etree.ElementTree as ET


class Track:
    def __init__(self, session, element=None, name=None):
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
        self._on_modify = None
        self.requires_audio_save = False
        if self.is_audacity_project:
            self._audio = self.audacity_project.as_audio_clip()
            self._audio.writeable = False
        else:
            try:
                self._audio = AudioClip.from_soundfile(self.filename)
                self._audio.writeable = False
            except FileNotFoundError:
                self._audio = None

    @property
    def on_modify(self):
        return self._on_modify

    @on_modify.setter
    def on_modify(self, callback):
        self._on_modify = callback

    def notify_modified(self):
        if self._on_modify is not None:
            self._on_modify()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.notify_modified()

    @property
    def filename(self):
        return os.path.join(
            os.path.dirname(self._session.session_file_path), self.name + ".flac")

    def get_audio_clip(self):
        return self._audio

    @property
    def is_rec(self):
        return self._is_rec

    @is_rec.setter
    def is_rec(self, enabled):
        self._is_rec = enabled
        self.notify_modified()

    @property
    def is_mute(self):
        return self._is_mute

    @is_mute.setter
    def is_mute(self, enabled):
        self._is_mute = enabled
        self.notify_modified()

    @property
    def is_solo(self):
        return self._is_solo

    @is_solo.setter
    def is_solo(self, enabled):
        self._is_solo = enabled
        self.notify_modified()

    @property
    def rec_source(self):
        return self._rec_source

    @rec_source.setter
    def rec_source(self, value):
        self._rec_source = value
        self.notify_modified()

    @property
    def source(self):
        return self._source

    @property
    def is_audacity_project(self):
        return self._source == "audacity-project"

    @property
    def audacity_project(self):
        return self._audacity_project

    @property
    def beats_in_audacity_beat(self):
        return self._beats_in_audacity_beat

    @property
    def timing(self):
        if self.is_audacity_project:
            return AudacityTiming(self._audacity_project)
        else:
            return self._session.timing

    @property
    def fader(self):
        return self._fader

    def to_js(self):
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
    def __init__(self, session_file_path):
        assert os.path.exists(session_file_path)
        if os.path.isdir(session_file_path):
            self._session_file_path = os.path.join(
                os.path.curdir, session_file_path, "session.mnk")
        else:
            self._session_file_path = os.path.join(
                os.path.curdir, session_file_path)
        et = ET.parse(self._session_file_path)
        self._session_format_name = et.getroot().attrib['format-name']
        self._session_format_version = et.getroot().attrib['format-version']
        self._modified_with = et.getroot().find(
            'program-version').attrib['modified-with']
        self._configuration = {
            element.attrib['name']: element.attrib['value']
            for element
            in et.getroot().find('configuration').findall('setting')}
        self._marks = {element.attrib['name']: element.attrib['position']
                       for element
                       in et.getroot().find('marks').findall('mark')}
        self._tracks = [Track(self, element) for element
                        in et.getroot().find('tracks').findall('track')]
        for track in self._tracks:
            track.on_modify = self._onModified
        self._are_controls_modified = False
        self._on_modify = None

    def save(self):
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

        tree = ET.ElementTree(root)
        tree.write(self._session_file_path)
        self._are_controls_modified = False

    @property
    def on_modify(self):
        return self._on_modify

    @on_modify.setter
    def on_modify(self, callback):
        self._on_modify = callback

    @property
    def are_controls_modified(self):
        return self._are_controls_modified

    def _onModified(self):
        self._are_controls_modified = True
        if self._on_modify is not None:
            self._on_modify()

    @property
    def session_file_path(self):
        return self._session_file_path

    @property
    def name(self):
        # TODO: Store the session name inside the session file
        return os.path.basename(os.path.dirname(self._session_file_path))

    @property
    def session_format_name(self):
        return self._session_format_name

    @property
    def session_format_version(self):
        return self._session_format_version

    @property
    def modified_with(self):
        return self._modified_with

    @property
    def configuration(self):
        return self._configuration

    @property
    def marks(self):
        return self._marks

    @property
    def tracks(self):
        return self._tracks

    def track_for_name(self, name):
        for track in self._tracks:
            if track.name == name:
                return track

    def _index_of_track(self, name):
        for i, track in enumerate(self._tracks):
            if track.name == name:
                return i

    def remove_track(self, name):
        i = self._index_of_track(name)
        if i is not None:
            del self._tracks[i]
        self._onModified()

    def move_track_up(self, name):
        i = self._index_of_track(name)
        if i is None or i == 0:
            return  # can't move the track up
        self._tracks[i - 1], self._tracks[i] = (
            self._tracks[i], self._tracks[i - 1])
        self._onModified()

    def move_track_down(self, name):
        i = self._index_of_track(name)
        if i is None or i == len(self._tracks) - 1:
            return  # can't move the track down
        self._tracks[i + 1], self._tracks[i] = (
            self._tracks[i], self._tracks[i + 1])
        self._onModified()

    def add_track(self, name):
        self._tracks.append(Track(self, element=None, name=name))
        self._onModified()

    @property
    def bpm(self):
        return float(self.configuration['bpm'])

    @property
    def time_signature(self):
        return int(self.configuration['time_sig'])

    @property
    def timing(self):
        return FixedBpmTiming(self.bpm)

    @property
    def track_timings(self):
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

    def make_playspec_from_tracks(self, amio_interface, metronome, tracks):
        playspec_generator = PlayspecGenerator(amio_interface)
        playspec_generator.add_source(SessionTracksPlayspecSource(tracks))
        playspec_generator.add_source(MetronomePlayspecSource(self, metronome))
        return playspec_generator.make_playspec()

    def to_js(self):
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
