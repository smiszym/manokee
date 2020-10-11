from collections import namedtuple
from manokee.input_recorder import InputRecorder
from manokee.session_holder import SessionHolder
from manokee.track import Track
from typing import Dict


class AudioSubstitute(namedtuple("AudioSubstitute", "clip starting_frame")):
    pass


class Reviser:
    def __init__(self, session_holder: SessionHolder, input_recorder: InputRecorder):
        self.audio_substitutes: Dict[Track, AudioSubstitute] = {}
        self._session_holder = session_holder
        self._input_recorder = input_recorder
        self._session_holder.add_observer(self._create_audio_substitutes)
        self._input_recorder.add_observer(self._create_audio_substitutes)

    def _create_audio_substitutes(self):
        fragment = self._input_recorder.fragment_being_revised
        session = self._session_holder.session
        if fragment is None or session is None:
            self.audio_substitutes = {}
            return
        left = fragment.as_clip().channel(0)
        right = fragment.as_clip().channel(1)
        self.audio_substitutes = {
            track: AudioSubstitute(
                left if track.rec_source == "L" else right, fragment.starting_frame
            )
            for track in session.tracks
            if track.is_rec
        }
