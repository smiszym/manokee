from amio import Playspec
from manokee.playspec_source import PlayspecSource


class PlayspecGenerator:
    def __init__(self, amio_interface):
        self._amio_interface = amio_interface
        self._sources = []

    def add_source(self, source: PlayspecSource):
        self._sources.append(source)

    def make_playspec(self, length=600) -> Playspec:
        total_entries = sum(
            source.number_of_entries() for source in self._sources)
        playspec = Playspec(self._amio_interface, total_entries)
        playspec.set_length(self._amio_interface.secs_to_frame(length))
        current_entry = 0
        for source in self._sources:
            entries_needed = source.number_of_entries()
            for i in range(entries_needed):
                entry = source.create_entry(i)
                if entry is not None:
                    playspec.set_entry(current_entry,
                                       entry.clip, entry.frame_a, entry.frame_b,
                                       entry.play_at_frame, entry.repeat_interval,
                                       entry.gain_l, entry.gain_r)
                current_entry += 1
        return playspec
