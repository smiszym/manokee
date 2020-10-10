from amio import Interface, Playspec
import logging
from manokee.metronome import Metronome
from manokee.session import Session
from manokee.track import Track
from manokee.session_holder import SessionHolder
from manokee.timing.timing import Timing
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.interpolated_timing import InterpolatedTiming
from typing import Optional


class PlayspecController:
    def __init__(self, amio_interface: Interface):
        self._amio_interface = amio_interface
        self._metronome = None
        self.on_session_change = None
        self._playspec: Optional[Playspec] = None
        self._timing: Timing = FixedBpmTiming()
        self._active_track_group_name = ""
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
        self._playspecs_for_groups = {
            group_name: session.make_playspec_for_track_group(
                            self._amio_interface, self._metronome, group_name)
            for group_name in self._session_holder.session.track_group_names
        }
        self._playspec = self._playspecs_for_groups[""]
        self._amio_interface.set_current_playspec(self._playspec)

    @property
    def timing(self) -> Timing:
        return self._timing

    @property
    def active_track_group_name(self) -> str:
        return self._active_track_group_name

    @active_track_group_name.setter
    def active_track_group_name(self, group_name: str):
        old_timing = self._timing
        if group_name == "":
            self._timing = self._session_holder.session.timing
        else:
            track = self._session_holder.session.track_for_name(group_name)
            if track is None:
                raise ValueError(f"No such track: {group_name}")
            self._timing = (InterpolatedTiming(
                track.timing, track.beats_in_audacity_beat))
        new_timing = self._timing
        self._active_track_group_name = group_name
        self._playspec = self._playspecs_for_groups[group_name]
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
