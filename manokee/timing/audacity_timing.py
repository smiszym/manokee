from manokee.audacity.project import AudacityProject
from manokee.timing.timing import Timing
import re


class AudacityTiming(Timing):
    def __init__(self, project: AudacityProject):
        label_track = project.get_label_track()
        # If the label track has name "offset=130",
        # there will be 130 ms offset applied to labels
        m = re.search("=(\d+)", label_track.get_name())
        offset = 0
        if m:
            offset = int(m.group(1))
        self.b = [pos - offset / 1000 for pos in label_track.get_label_positions()]

    def beat_to_seconds(self, beat_number: float) -> float:
        beat_a = int(beat_number)
        beat_b = beat_a + 1
        remainder = beat_number - beat_a
        sec_a = self.b[beat_a]
        sec_b = self.b[beat_b]
        return sec_a + (sec_b - sec_a) * remainder

    def seconds_to_beat(self, time: float) -> float:
        beat_a = self._seconds_to_beat_integer(time)
        beat_b = beat_a + 1
        sec_a = self.beat_to_seconds(beat_a)
        sec_b = self.beat_to_seconds(beat_b)
        return beat_a + (time - sec_a) / (sec_b - sec_a)

    def _seconds_to_beat_integer(self, time: float) -> int:
        i = 0
        while i < len(self.b) and self.b[i] < time:
            i += 1
        return i - 1 if i > 0 else 0
