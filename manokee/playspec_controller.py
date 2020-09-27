from amio import Interface, Playspec
import logging
from manokee.metronome import Metronome
from manokee.session import Session, Track
from manokee.session_holder import SessionHolder
from manokee.timing.timing import Timing
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.interpolated_timing import InterpolatedTiming
from typing import Optional


class PlayspecController:
    def __init__(self, amio_interface: Interface):
        self._amio_interface = amio_interface
        self._metronome = None
        self._first_audacity_track: Optional[Track] = None
        self.on_session_change = None
        self._playspec: Optional[Playspec] = None
        self._timing: Timing = FixedBpmTiming()
        self._is_audacity_timing_on = False
        self._session_holder = SessionHolder()
        self._session_holder.on_session_change = self._on_session_changed
        # TODO Make it possible to open a session without specifying frame rate
        self._session_holder.session = Session(
            self._amio_interface.get_frame_rate()
            if self._amio_interface is not None
            else 48000)

    def _on_session_changed(self):
        self._session_holder.session.on_modify = (
            self._schedule_playspecs_recreation)
        self._metronome = Metronome(
            self._amio_interface, self._session_holder.session)
        self._find_first_audacity_track()
        self._timing = self._session_holder.session.timing
        self._recreate_playspecs()
        if self.on_session_change is not None:
            self.on_session_change()

    @property
    def session(self) -> Session:
        return self._session_holder.session

    @session.setter
    def session(self, session: Session):
        self._session_holder.session = session

    def _schedule_playspecs_recreation(self):
        # TODO: Move this to a background thread
        self._recreate_playspecs()

    def _recreate_playspecs(self):
        session = self._session_holder.session
        self._fixed_bpm_playspec = session.make_playspec_from_tracks(
                self._amio_interface,
                self._metronome,
                (track for track in session.tracks
                 if not track.is_audacity_project))
        self._audacity_playspec = session.make_playspec_from_tracks(
            self._amio_interface,
            self._metronome,
            (track for track in session.tracks
             if track.is_audacity_project))
        self._playspec = self._fixed_bpm_playspec
        self._amio_interface.set_current_playspec(self._playspec)

    @property
    def timing(self) -> Timing:
        return self._timing

    @property
    def is_audacity_timing_on(self) -> bool:
        return self._is_audacity_timing_on

    @is_audacity_timing_on.setter
    def is_audacity_timing_on(self, want_audacity_timing: bool):
        old_timing = self._timing
        if self._first_audacity_track is None:
            if want_audacity_timing:
                raise ValueError(
                    'Cannot set Audacity timing: no Audacity track')
            self._timing = self._session_holder.session.timing
        else:
            self._timing = (InterpolatedTiming(
                self._first_audacity_track.timing,
                self._first_audacity_track.beats_in_audacity_beat)
                            if want_audacity_timing
                            else self._session_holder.session.timing)
        new_timing = self._timing
        self._is_audacity_timing_on = want_audacity_timing
        self._playspec = (self._audacity_playspec
                          if self._is_audacity_timing_on
                          else self._fixed_bpm_playspec)
        current_frame = self._amio_interface.get_position()
        current_second = self._amio_interface.frame_to_secs(current_frame)
        beat = int(old_timing.seconds_to_beat(current_second))
        insert_beat = beat + 1  # TODO Handle very short beats
        insert_second = old_timing.beat_to_seconds(insert_beat)
        insert_frame = self._amio_interface.secs_to_frame(insert_second)
        new_second = new_timing.beat_to_seconds(insert_beat)
        new_frame = self._amio_interface.secs_to_frame(new_second)
        logging.info(f"Current position is {current_second} s, which is {beat} beat, "
              f"so we'll switch on {insert_beat} beat, which corresponds to "
              f"{new_second} s in the new timing which is "
              f"beat {new_timing.seconds_to_beat(new_second)}.")
        logging.info(f"Insert frame = {insert_frame}; new frame = {new_frame}")
        self._playspec.set_insertion_points(insert_frame, new_frame)
        self._amio_interface.set_current_playspec(self._playspec)

    def _find_first_audacity_track(self):
        self._first_audacity_track = None
        for track in self.session.tracks:
            if track.is_audacity_project:
                self._first_audacity_track = track
