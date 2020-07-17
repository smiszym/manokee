from manokee.timing.timing import Timing


class FixedBpmTiming(Timing):
    def __init__(self, bpm=120):
        self.bpm = bpm

    def beat_to_seconds(self, beat_number):
        return beat_number * 60 / self.bpm

    def seconds_to_beat(self, time):
        return time / 60 * self.bpm
