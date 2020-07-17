from manokee.timing.timing import Timing


class InterpolatedTiming(Timing):
    def __init__(self, original_timing, beats_in_beat):
        self._original_timing = original_timing
        self._beats_in_beat = beats_in_beat

    def beat_to_seconds(self, beat):
        beat_a = int(beat / self._beats_in_beat)
        remainder = beat - (beat_a * self._beats_in_beat)
        beat_b = beat_a + 1
        sec_a = self._original_timing.beat_to_seconds(beat_a)
        sec_b = self._original_timing.beat_to_seconds(beat_b)
        return sec_a + (sec_b - sec_a) * remainder / self._beats_in_beat

    def seconds_to_beat(self, time):
        return self._original_timing.seconds_to_beat(time) * self._beats_in_beat
