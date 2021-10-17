from math import floor

from manokee.audacity.project import AudacityProject
from manokee.timing.timing import Timing
import re


class AudacityTiming(Timing):
    def __init__(self, project: AudacityProject, *, beats_in_audacity_beat: int = 1):
        label_track = project.get_label_track()
        # If the label track has name "offset=130",
        # there will be 130 ms offset applied to labels
        m = re.search(r"=(\d+)", label_track.get_name())
        offset = 0
        if m:
            offset = int(m.group(1))
        self.b = [pos - offset / 1000 for pos in label_track.get_label_positions()]
        self.average_audacity_beat_length = (self.b[-1] - self.b[0]) / (len(self.b) - 1)
        self.average_beat_length = (
            self.average_audacity_beat_length / beats_in_audacity_beat
        )
        self.beats_in_audacity_beat = beats_in_audacity_beat

    def beat_to_seconds(self, beat_number: float) -> float:
        beat_number /= self.beats_in_audacity_beat
        beat_a = floor(beat_number)
        beat_b = beat_a + 1
        remainder = beat_number - beat_a
        sec_a = self._label_position_extrapolated(beat_a)
        sec_b = self._label_position_extrapolated(beat_b)
        return sec_a + (sec_b - sec_a) * remainder

    def seconds_to_beat(self, time: float) -> float:
        beat_a = self._seconds_to_beat_integer(time)
        beat_b = beat_a + 1
        sec_a = self._label_position_extrapolated(beat_a)
        sec_b = self._label_position_extrapolated(beat_b)
        return self.beats_in_audacity_beat * (beat_a + (time - sec_a) / (sec_b - sec_a))

    def _label_position_extrapolated(self, beat: int) -> float:
        if beat < 0:
            return self.b[0] + beat * self.average_audacity_beat_length
        elif beat >= len(self.b):
            return (
                self.b[-1]
                + (beat - len(self.b) + 1) * self.average_audacity_beat_length
            )
        else:
            return self.b[beat]

    def _seconds_to_beat_integer(self, time: float) -> int:
        i = 0
        while i < len(self.b) and self.b[i] < time:
            i += 1
        return i - 1 if i > 0 else 0
