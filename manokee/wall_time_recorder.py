from collections import namedtuple
from datetime import datetime, timedelta
import itertools
from typing import List, Optional


class WallTimeEntry(namedtuple("WallTimeEntry", "session_time start_time duration")):
    def left_trimmed(self, trim_at: timedelta) -> Optional["WallTimeEntry"]:
        trim_by = trim_at - self.session_time
        if trim_by <= timedelta(0):
            return self
        if self.duration - trim_by <= timedelta(0):
            return None
        return WallTimeEntry(
            trim_at, self.start_time + trim_by, self.duration - trim_by
        )

    def right_trimmed(self, trim_at: timedelta) -> Optional["WallTimeEntry"]:
        trim_by = self.session_time + self.duration - trim_at
        if trim_by <= timedelta(0):
            return self
        if self.duration - trim_by <= timedelta(0):
            return None
        return WallTimeEntry(
            self.session_time, self.start_time, self.duration - trim_by
        )


class WallTimeRecorder:
    def __init__(self, entries: Optional[List[WallTimeEntry]] = None):
        # Entries are kept non-overlapping
        self.entries: List[WallTimeEntry] = entries or []

    def add(self, session_time: timedelta, start_time: datetime, duration: timedelta):
        new_entry = WallTimeEntry(  # black: keep newline here
            session_time, start_time, duration
        ).left_trimmed(timedelta(0))
        self.entries = [
            entry
            for entry in itertools.chain(
                (entry.right_trimmed(session_time) for entry in self.entries),
                (new_entry,),
                (entry.left_trimmed(session_time + duration) for entry in self.entries),
            )
            if entry
        ]
