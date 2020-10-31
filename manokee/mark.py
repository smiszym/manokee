from enum import Enum
from manokee.time_formatting import format_seconds, parse_seconds
from typing import Optional


class MarkType(Enum):
    BEAT = 0
    SECONDS = 1

    def __str__(self):
        return self.name.lower()


class Mark:
    def __init__(self, *, beat=None, seconds=None, track_group=None):
        assert not (beat is None and seconds is None)
        assert beat is None or seconds is None
        if beat is not None:
            # For beat marks, only self.beat is set
            assert track_group is None
            if beat is None:
                beat = 0
        elif seconds is not None:
            # For seconds marks, self.seconds and self.track_group are set
            if seconds is None:
                seconds = 0
            if track_group is None:
                track_group = ""
        else:
            raise ValueError
        self.beat: Optional[int] = beat
        self.seconds: Optional[float] = seconds
        self.track_group: Optional[str] = track_group

    @property
    def mark_type(self):
        if self.beat is not None:
            return MarkType.BEAT
        elif self.seconds is not None:
            return MarkType.SECONDS
        else:
            raise ValueError

    @classmethod
    def from_str(cls, s):
        if s.startswith("beat "):
            return cls(beat=int(s[5:]))
        else:
            if " @ " in s:
                seconds, track_group = s.split(" @ ")
            else:
                seconds = s
                track_group = ""
            return cls(seconds=parse_seconds(seconds), track_group=track_group)

    def to_seconds(self, beat_to_seconds_converter) -> float:
        if self.mark_type == MarkType.BEAT:
            return beat_to_seconds_converter(self.beat)
        elif self.mark_type == MarkType.SECONDS:
            return self.seconds  # type: ignore
        else:
            raise ValueError

    def __str__(self):
        if self.mark_type == MarkType.BEAT:
            return f"beat {self.beat}"
        elif self.mark_type == MarkType.SECONDS:
            if self.track_group != "":
                return f"{format_seconds(self.seconds)} @ {self.track_group}"
            else:
                return format_seconds(self.seconds)
        else:
            raise ValueError

    def __eq__(self, other):
        if type(self) is type(other):
            return (
                self.beat == other.beat
                and self.seconds == other.seconds
                and self.track_group == other.track_group
            )
        return False

    def __hash__(self):
        return hash((self.beat, self.seconds, self.track_group))
