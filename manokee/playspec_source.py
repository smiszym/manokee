from amio import AudioClip, Fader
from collections import namedtuple
import manokee.metronome
import manokee.session
import manokee.track
from typing import Iterable


class PlayspecEntry(namedtuple(
        'PlayspecEntry',
        'clip frame_a frame_b play_at_frame repeat_interval gain_l gain_r')):
    pass


class PlayspecSource:
    def number_of_entries(self) -> int:
        """
        TODO This API will be greatly simplified once Playspec objects
        are mergable.
        :return: The number of playspec entries this PlayspecSource creates.
        """
        raise NotImplementedError

    def create_entry(self, entry_number: int) -> PlayspecEntry:
        """
        TODO This API will be greatly simplified once Playspec objects
        are mergable.
        :param entry_number: The index of the entry to generate, from 0
        to (number_of_entries()-1)
        :return: A PlayspecEntry object that can be inserted to a Playspec.
        """
        raise NotImplementedError


class SessionTracksPlayspecSource(PlayspecSource):
    def __init__(self, tracks: Iterable['manokee.track.Track']):
        self._tracks = list(tracks)
        self._is_soloed = any(track.is_solo for track in self._tracks)
        self._additional_data = {track: {"audible":
                                         track.is_solo if self._is_soloed
                                         else not track.is_mute}
                                 for track in self._tracks}

    def number_of_entries(self) -> int:
        return len(self._tracks)

    def create_entry(self, entry_number: int) -> PlayspecEntry:
        track = self._tracks[entry_number]
        clip = track.get_audio_clip()
        if clip is None:
            # TODO Don't hardcode 48 kHz: a) implement support for entries
            # with different frame rates; b) add a special AudioClip
            # instance being "silence", which simply is a no-op when mixed
            return PlayspecEntry(AudioClip.zeros(1, 1, 48000), 0, 1, 0, 0,
                                 0.0, 0.0)
        if self._additional_data[track]["audible"]:
            fader = track.fader
        else:
            fader = Fader(float('-inf'))
        return PlayspecEntry(clip, 0, len(clip), 0, 0,
                             fader.left_gain_factor,
                             fader.right_gain_factor)


class MetronomePlayspecSource(PlayspecSource):
    def __init__(self, session: 'manokee.session.Session',
                 metronome: 'manokee.metronome.Metronome'):
        self._metronome = metronome
        self._metronome_enabled = session.configuration['metronome'] == "1"
        self._metronome_fader = Fader(
            float(session.configuration['metronome_vol']),
            float(session.configuration['metronome_pan']))

    def number_of_entries(self) -> int:
        return 1 if self._metronome_enabled else 0

    def create_entry(self, entry_number: int) -> PlayspecEntry:
        assert entry_number == 0
        assert self._metronome_enabled
        metronome_clip = self._metronome.audio_clip
        return PlayspecEntry(metronome_clip,
                           0, len(metronome_clip),
                           0, len(metronome_clip),
                           self._metronome_fader.left_gain_factor,
                           self._metronome_fader.right_gain_factor)
