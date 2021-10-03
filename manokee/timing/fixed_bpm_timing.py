from manokee.timing.timing import Timing


class FixedBpmTiming(Timing):
    def __init__(self, bpm: float = 120):
        self.bpm: float = bpm
        self.average_beat_length: float = 60 / bpm

    def beat_to_seconds(self, beat_number: float) -> float:
        return beat_number * 60 / self.bpm

    def seconds_to_beat(self, time: float) -> float:
        return time / 60 * self.bpm
