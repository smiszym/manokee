from amio import AudioClip, InputAudioChunk, Interface
from collections import deque
import itertools
from typing import Optional, List

from manokee.meter import Meter
from manokee.time_formatting import format_frame
from manokee.transport_state import TransportState


class InputFragment:
    def __init__(self, id: int, is_recording: bool):
        self._id = id
        self._chunks: List[InputAudioChunk] = []
        self._was_transport_rolling = None
        self._is_recording = is_recording
        self._stop_frame = None
        self._length = 0

    def __len__(self) -> int:
        return self._length

    @property
    def id(self) -> int:
        return self._id

    @property
    def is_empty(self) -> bool:
        return len(self._chunks) == 0

    @property
    def chunks(self) -> List[InputAudioChunk]:
        return self._chunks

    @property
    def transport_state(self) -> TransportState:
        if self._was_transport_rolling:
            return (
                TransportState.RECORDING
                if self._is_recording
                else TransportState.ROLLING
            )
        else:
            return TransportState.STOPPED

    @property
    def starting_frame(self) -> Optional[int]:
        if len(self._chunks) > 0:
            return self._chunks[0].starting_frame
        return None

    def is_chunk_compatible(self, chunk: InputAudioChunk) -> bool:
        return (
            self._was_transport_rolling is None
            or self._was_transport_rolling == chunk.was_transport_rolling
        )

    def append_chunk(self, chunk: InputAudioChunk):
        assert self.is_chunk_compatible(chunk)
        self._chunks.append(chunk)
        self._was_transport_rolling = chunk.was_transport_rolling
        self._stop_frame = chunk.starting_frame + len(chunk)
        self._length += len(chunk)

    def last_chunk_wall_time(self):
        return self._chunks[-1].wall_time

    def cut(self, desired_length: int):
        # This will cut to a bit longer fragment than desired_length,
        # because it won't cut individual chunks.
        while len(self._chunks) > 1 and desired_length < len(self) - len(
            self._chunks[-1]
        ):
            chunk = self._chunks.pop(0)
            self._length -= len(chunk)

    def as_clip(self) -> AudioClip:
        return AudioClip.concatenate(self._chunks)

    def to_js(self, amio_interface: Interface) -> dict:
        result = {
            "id": self._id,
            "transport_state": str(self.transport_state),
            "length": format_frame(amio_interface, len(self)),
        }
        if self.starting_frame is not None:
            result["starting_time"] = format_frame(amio_interface, self.starting_frame)
        return result


class InputRecorder:
    def __init__(self, keepalive_mins: float, keepalive_margin_mins: float):
        self._id_generator = itertools.count()
        self._input_fragments = deque([InputFragment(next(self._id_generator), False)])
        self._is_recording = False
        self._meter = Meter(2)
        self._keepalive_mins = keepalive_mins
        self._keepalive_margin_mins = keepalive_margin_mins
        self._wall_time_approx = None

    @property
    def meter(self) -> Meter:
        return self._meter

    @property
    def fragments(self) -> List[InputFragment]:
        return list(self._input_fragments)

    @property
    def last_fragment(self) -> InputFragment:
        return self._input_fragments[0]

    def fragment_by_id(self, id: int) -> Optional[InputFragment]:
        for fragment in self._input_fragments:
            if fragment.id == id:
                return fragment
        return None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        self._is_recording = value

    def append_input_chunk(self, input_chunk: InputAudioChunk):
        self._update_meter(input_chunk)
        if (
            self.last_fragment.transport_state != TransportState.STOPPED
            and not input_chunk.was_transport_rolling
        ):
            # Stop recording when AMIO transport stops rolling
            self._is_recording = False
        if not self.last_fragment.is_chunk_compatible(input_chunk):
            self._input_fragments.appendleft(
                InputFragment(next(self._id_generator), self._is_recording)
            )
        self.last_fragment.append_chunk(input_chunk)
        # Keep track of what the current wall time is (approximately)
        self._wall_time_approx = input_chunk.wall_time

    def remove_old_fragments(self, amio_interface: Interface):
        # Discard old fragments, but keep at least 1 fragment
        index = self._first_to_discard(60 * self._keepalive_mins)
        last_recording_fragment = None
        if index is not None and index >= 1:
            while len(self._input_fragments) > index:
                fragment = self._input_fragments.pop()
                if fragment.transport_state == TransportState.RECORDING:
                    last_recording_fragment = fragment
            # If no recording fragment remained, append the last removed
            # recording fragment
            if last_recording_fragment is not None and not any(
                fragment.transport_state == TransportState.RECORDING
                for fragment in self._input_fragments
            ):
                self._input_fragments.append(last_recording_fragment)

        total_length = sum(len(fragment) for fragment in self._input_fragments)
        last_fragment_length = len(self._input_fragments[-1])
        # Cut the last fragment if too long
        total_allowed = amio_interface.secs_to_frame(
            60 * (self._keepalive_mins + self._keepalive_margin_mins)
        )
        fragment_to_cut = self._input_fragments[-1]
        if fragment_to_cut.transport_state != TransportState.RECORDING:
            fragment_to_cut.cut(total_allowed - (total_length - last_fragment_length))

    def _first_to_discard(self, discard_threshold: float) -> Optional[int]:
        if self._wall_time_approx is None:
            return None
        for i, fragment in enumerate(self._input_fragments):
            if (
                self._wall_time_approx - fragment.last_chunk_wall_time()
            ).total_seconds() >= discard_threshold:
                return i
        return None

    def _update_meter(self, input_chunk: InputAudioChunk):
        _, left_rms, left_peak = input_chunk.channel(0).create_metering_data()
        _, right_rms, right_peak = input_chunk.channel(1).create_metering_data()
        self._meter.current_rms_dB = [float(max(left_rms)), float(max(right_rms))]
        self._meter.current_peak_dB = [float(max(left_peak)), float(max(right_peak))]
