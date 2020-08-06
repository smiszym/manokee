from amio import AudioClip
from collections import deque
from datetime import datetime
from manokee.meter import Meter
from manokee.time_formatting import format_frame
from manokee.transport_state import TransportState


class InputFragment:
    def __init__(self, id, is_recording):
        self._id = id
        self._chunks = []
        self._was_transport_rolling = None
        self._is_recording = is_recording
        self._stop_frame = None
        self._length = 0

    def __len__(self):
        return self._length

    @property
    def id(self):
        return self._id

    @property
    def is_empty(self):
        return len(self._chunks) == 0

    @property
    def chunks(self):
        return self._chunks

    @property
    def transport_state(self):
        if self._was_transport_rolling:
            return (TransportState.RECORDING if self._is_recording
                    else TransportState.ROLLING)
        else:
            return TransportState.STOPPED

    @property
    def starting_frame(self):
        if len(self._chunks) > 0:
            return self._chunks[0].starting_frame

    def is_chunk_compatible(self, chunk):
        return (self._was_transport_rolling is None
                or self._was_transport_rolling == chunk.was_transport_rolling)

    def append_chunk(self, chunk):
        assert self.is_chunk_compatible(chunk)
        self._chunks.append(chunk)
        self._was_transport_rolling = chunk.was_transport_rolling
        self._stop_frame = chunk.starting_frame + len(chunk)
        self._length += len(chunk)

    def last_chunk_wall_time(self):
        return self._chunks[-1].wall_time

    def cut(self, desired_length):
        # This will cut to a bit longer fragment than desired_length,
        # because it won't cut individual chunks.
        while (len(self._chunks) > 1
               and desired_length < len(self) - len(self._chunks[-1])):
            chunk = self._chunks.pop(0)
            self._length -= len(chunk)

    def as_clip(self):
        return AudioClip.concatenate(self._chunks)

    def to_js(self, amio_interface):
        result = {'id': self._id,
                  'transport_state': str(self.transport_state),
                  'length': format_frame(amio_interface, len(self)),
                  }
        starting_frame = self.starting_frame
        if starting_frame is not None:
            result['starting_time'] = format_frame(
                amio_interface, self.starting_frame)
        return result


class InputRecorder:
    def __init__(self, keepalive_mins, keepalive_margin_mins):
        self._input_fragments = deque([InputFragment(0, False)])
        self._is_recording = False
        self._meter = Meter(2)
        self._keepalive_mins = keepalive_mins
        self._keepalive_margin_mins = keepalive_margin_mins
        self._wall_time_approx = None

    @property
    def meter(self):
        return self._meter

    @property
    def fragments(self):
        return list(self._input_fragments)

    @property
    def last_fragment(self):
        return self._input_fragments[0]

    def fragment_by_id(self, id):
        for fragment in self._input_fragments:
            if fragment.id == id:
                return fragment

    @property
    def is_recording(self):
        return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        self._is_recording = value

    def append_input_chunk(self, input_chunk):
        self._update_meter(input_chunk)
        if (self.last_fragment.transport_state != TransportState.STOPPED
                and not input_chunk.was_transport_rolling):
            # Stop recording when AMIO transport stops rolling
            self._is_recording = False
        if not self.last_fragment.is_chunk_compatible(input_chunk):
            self._input_fragments.appendleft(InputFragment(
                len(self._input_fragments), self._is_recording))
        self.last_fragment.append_chunk(input_chunk)
        # Keep track of what the current wall time is (approximately)
        self._wall_time_approx = input_chunk.wall_time

    def remove_old_fragments(self, amio_interface):
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
            if not any(fragment.transport_state == TransportState.RECORDING
                       for fragment in self._input_fragments):
                self._input_fragments.append(last_recording_fragment)

        total_length = sum(len(fragment) for fragment in self._input_fragments)
        last_fragment_length = len(self._input_fragments[-1])
        # Cut the last fragment if too long
        total_allowed = amio_interface.secs_to_frame(
            60 * (self._keepalive_mins + self._keepalive_margin_mins))
        self._input_fragments[-1].cut(
            total_allowed - (total_length - last_fragment_length))

    def _first_to_discard(self, discard_threshold):
        if self._wall_time_approx is None:
            return
        for i, fragment in enumerate(self._input_fragments):
            if ((self._wall_time_approx - fragment.last_chunk_wall_time())
                    .total_seconds() >= discard_threshold):
                return i

    def _update_meter(self, input_chunk):
        left_x, left_Y = input_chunk.channel(0).create_metering_data()
        right_x, right_Y = input_chunk.channel(1).create_metering_data()
        self._meter.current_rms_dB = [max(left_Y), max(right_Y)]
