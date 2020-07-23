from amio import AudioClip
from collections import deque
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
    def __init__(self, io_interface):
        self._input_fragments = deque([InputFragment(0, False)])
        self._io_interface = io_interface
        self._is_recording = False
        self._meter = Meter(2)

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
        if not self.last_fragment.is_chunk_compatible(input_chunk):
            if (self.last_fragment.transport_state != TransportState.STOPPED
                    and not input_chunk.was_transport_rolling):
                # Stop recording when AMIO transport stops rolling
                self._is_recording = False
            self._input_fragments.appendleft(InputFragment(
                len(self._input_fragments), self._is_recording))
        self.last_fragment.append_chunk(input_chunk)

    def _update_meter(self, input_chunk):
        left_x, left_Y = input_chunk.channel(0).create_metering_data()
        right_x, right_Y = input_chunk.channel(1).create_metering_data()
        self._meter.current_rms_dB = [max(left_Y), max(right_Y)]
