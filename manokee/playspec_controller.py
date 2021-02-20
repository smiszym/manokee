from amio import Interface, Playspec
from manokee.session import Session
from manokee.session_holder import SessionHolder
from manokee.timing.timing import Timing
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing_utils import calculate_insertion_points
from typing import Dict


class PlayspecController:
    def __init__(self, amio_interface: Interface, session_holder: SessionHolder):
        self._amio_interface = amio_interface
        self.on_session_change = None
        self._playspecs_for_groups: Dict[str, Playspec] = {}
        self._timing: Timing = FixedBpmTiming()
        self._active_track_group_name = ""
        self._session_holder = session_holder
        self._session_holder.on_session_change = self._on_session_changed

    def _on_session_changed(self):
        session = self._session_holder.session
        if session is not None:
            session.on_modify = self._schedule_playspecs_recreation
            self._timing = session.timing
            self._schedule_playspecs_recreation()
        else:
            self._timing = FixedBpmTiming()
            self._playspecs_for_groups = {}
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
        self._playspecs_for_groups = (
            self._session_holder.session.make_playspecs_for_track_groups(
                self._amio_interface
            )
        )
        current_playspec = self._playspecs_for_groups[self._active_track_group_name]
        self._amio_interface.schedule_playspec_change(current_playspec, 0, 0, None)

    @property
    def timing(self) -> Timing:
        return self._timing

    @property
    def active_track_group_name(self) -> str:
        return self._active_track_group_name

    @active_track_group_name.setter
    def active_track_group_name(self, group_name: str):
        old_timing = self._timing
        self._timing = self._session_holder.session.group_timing(group_name)
        new_timing = self._timing
        self._active_track_group_name = group_name
        insertion_points = calculate_insertion_points(
            self._amio_interface,
            self._amio_interface.get_position(),
            old_timing,
            new_timing,
        )
        current_playspec = self._playspecs_for_groups[self._active_track_group_name]
        self._amio_interface.schedule_playspec_change(
            current_playspec,
            insertion_points.insert_at,
            insertion_points.start_from,
            None,
        )
