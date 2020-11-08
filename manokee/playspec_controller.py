from amio import Interface, Playspec
from itertools import cycle
from manokee.looping import LoopFragment
from manokee.session_holder import SessionHolder
from manokee.timing.timing import Timing
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing_utils import calculate_insertion_points
from typing import Dict, Iterator, List, Optional

LoopSpec = List[LoopFragment]


class PlayspecController:
    def __init__(self, amio_interface: Interface, session_holder: SessionHolder):
        self._amio_interface = amio_interface
        self._playspecs_for_groups: Dict[str, Playspec] = {}
        self._timing: Timing = FixedBpmTiming()
        # One of _active_track_group_name and _loop_spec is not None
        self._active_track_group_name: Optional[str] = ""
        self._loop_spec: Optional[LoopSpec] = None
        self._loop_iterator: Optional[Iterator[LoopFragment]] = None
        self._current_loop_fragment: Optional[LoopFragment] = None
        self._session_holder = session_holder
        self._session_holder.add_observer(self._on_session_changed)
        self._is_recording = False

    def _on_session_changed(self):
        session = self._session_holder.session
        if session is not None:
            session.add_observer(self._schedule_playspecs_recreation)
            self._timing = session.timing
            self._schedule_playspecs_recreation()
        else:
            self._timing = FixedBpmTiming()
            self._playspecs_for_groups = {}

    def _schedule_playspecs_recreation(self):
        # TODO: Move this to a background thread
        session = self._session_holder.session
        self._playspecs_for_groups = {
            group_name: session.make_playspec_for_track_group(
                group_name, self._is_recording
            )
            for group_name in session.track_group_names
        }
        current_playspec = self._playspecs_for_groups[self._active_track_group_name]
        self._amio_interface.schedule_playspec_change(current_playspec, 0, 0, None)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        self._is_recording = value
        self._schedule_playspecs_recreation()

    @property
    def timing(self) -> Timing:
        return self._timing

    def plays_main_track_group(self) -> bool:
        return self._active_track_group_name == ""

    def set_active_track_group_name(self, group_name: str):
        old_timing = self._timing
        self._timing = self._session_holder.session.group_timing(group_name)
        new_timing = self._timing
        self._active_track_group_name = group_name
        self._loop_spec = None
        self._loop_iterator = None
        self._current_loop_fragment = None
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

    def set_loop_spec(self, loop_spec: LoopSpec):
        self._loop_spec = loop_spec
        self._loop_iterator = cycle(loop_spec)
        self._active_track_group_name = None
        self._schedule_next_fragment()

    def _schedule_next_fragment(self):
        if self._loop_spec is None:
            # The loop has been canceled in the meantime and we just have a regular
            # active track group now; nothing to do
            return
        old_fragment = self._current_loop_fragment
        self._current_loop_fragment = next(self._loop_iterator)
        new_fragment = self._current_loop_fragment
        old_timing = self._timing
        self._timing = self._session_holder.session.group_timing(
            new_fragment.track_group_name
        )
        new_timing = self._timing
        if old_fragment is not None:
            insert_at_frame = old_timing.beat_to_seconds(old_fragment.bar_b)
        else:
            insert_at_frame = 0
        start_from_frame = new_timing.beat_to_seconds(new_fragment.bar_a)
        insert_frame = self._amio_interface.secs_to_frame(insert_at_frame)
        new_frame = self._amio_interface.secs_to_frame(start_from_frame)
        current_playspec = self._playspecs_for_groups[new_fragment.track_group_name]
        self._amio_interface.schedule_playspec_change(
            current_playspec, insert_frame, new_frame, self._on_playspec_set
        )

    def _on_playspec_set(self, successfully):
        if successfully:
            self._schedule_next_fragment()
