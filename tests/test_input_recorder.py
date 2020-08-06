from amio import create_io_interface
from manokee.input_recorder import InputRecorder
import pytest


@pytest.mark.parametrize("length_min,length_max", [(4, 6), (2, 3), (3, 7)])
def test_removing_old_fragments(length_min, length_max):
    recorder = InputRecorder(length_min, length_max - length_min)
    amio_interface = create_io_interface('null', frame_rate=48000)
    amio_interface.input_chunk_callback = recorder.append_input_chunk
    amio_interface.set_transport_rolling(True)
    while (amio_interface.frame_to_secs(amio_interface.get_position())
           < (length_max + 2) * 60):
        amio_interface.advance_single_chunk_length()
    recorder.remove_old_fragments(amio_interface)
    for fragment in recorder.fragments:
        assert fragment is not None
    total_recorded_len = sum(len(fragment) for fragment in recorder.fragments)
    total_recorded_mins = total_recorded_len / 48000 / 60
    tolerance_mins = 0.5
    assert (length_min - tolerance_mins
            <= total_recorded_mins
            <= length_max + tolerance_mins)
