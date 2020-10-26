from amio import Interface
from manokee.timing.timing import Timing


class AmioTiming(Timing):
    """
    A wrapper around a Timing object that is associated with an AMIO interface
    and provides conversion methods to and from frames.
    """

    def __init__(self, timing: Timing, amio_interface: Interface):
        self.timing = timing
        self.amio_interface = amio_interface

    def beat_to_seconds(self, beat_number: float) -> float:
        return self.timing.beat_to_seconds(beat_number)

    def seconds_to_beat(self, time: float) -> float:
        return self.timing.seconds_to_beat(time)

    def frames_to_seconds(self, frames: int) -> float:
        return self.amio_interface.frame_to_secs(frames)

    def frames_to_beats(self, frames: int) -> float:
        return self.timing.seconds_to_beat(self.amio_interface.frame_to_secs(frames))

    def seconds_to_frames(self, seconds: float) -> int:
        return int(self.amio_interface.secs_to_frame(seconds))

    def beats_to_frames(self, beats: float) -> int:
        return int(
            self.amio_interface.secs_to_frame(self.timing.beat_to_seconds(beats))
        )
