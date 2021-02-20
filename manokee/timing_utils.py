from amio import Interface
from collections import namedtuple
from manokee.session import Session
from manokee.timing.timing import Timing
from typing import Tuple


class InsertionPoints(
    namedtuple("InsertionPoints", "insert_at start_from", defaults=(0, 0))
):
    pass


def frame_to_beat_number(
    amio_interface: Interface, timing: Timing, frame: int
) -> float:
    return timing.seconds_to_beat(amio_interface.frame_to_secs(frame))


def beat_number_to_frame(
    amio_interface: Interface, timing: Timing, beat_number: float
) -> int:
    return amio_interface.secs_to_frame(timing.beat_to_seconds(beat_number))


def frame_to_bar_beat(
    amio_interface: Interface, session: Session, timing: Timing, frame: int
) -> Tuple[int, int]:
    if session is None:
        return None, None
    absolute_beat = int(timing.seconds_to_beat(amio_interface.frame_to_secs(frame)))
    sig = session.time_signature
    return absolute_beat // sig, absolute_beat % sig


def calculate_insertion_points(amio_interface, old_frame, old_timing, new_timing):
    current_second = amio_interface.frame_to_secs(old_frame)
    beat = int(old_timing.seconds_to_beat(current_second))
    insert_beat = beat + 1  # TODO Handle very short beats
    insert_second = old_timing.beat_to_seconds(insert_beat)
    insert_frame = amio_interface.secs_to_frame(insert_second)
    new_second = new_timing.beat_to_seconds(insert_beat)
    new_frame = amio_interface.secs_to_frame(new_second)
    return InsertionPoints(insert_frame, new_frame)
