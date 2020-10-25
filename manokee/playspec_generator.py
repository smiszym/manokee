from amio import NativeInterface, Playspec, PlayspecEntry
from manokee.playspec_source import PlayspecSource
from typing import List


class PlayspecGenerator:
    def __init__(self, amio_interface: NativeInterface):
        self._amio_interface = amio_interface
        self._sources: List[PlayspecSource] = []

    def add_source(self, source: PlayspecSource):
        self._sources.append(source)

    def make_playspec(self) -> Playspec:
        total_entries = sum(source.number_of_entries() for source in self._sources)
        playspec: Playspec = [None for _ in range(total_entries)]
        current_entry = 0
        for source in self._sources:
            entries_needed = source.number_of_entries()
            for i in range(entries_needed):
                entry = source.create_entry(i)
                if entry is not None:
                    playspec[current_entry] = PlayspecEntry(
                        entry.clip,
                        entry.frame_a,
                        entry.frame_b,
                        entry.play_at_frame,
                        entry.repeat_interval,
                        entry.gain_l,
                        entry.gain_r,
                    )
                current_entry += 1
        return playspec
