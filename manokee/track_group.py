from typing import List, Optional

import manokee.metronome
import manokee.track


class TrackGroup:
    """
    Temporary object providing information about a track group in a session.
    The fields don't reflect any future changes in the session.
    """

    def __init__(self, *, name: str, session):
        self.name = name
        self.session = session
        if self.name == "":
            # The main track group
            self.tracks: List[manokee.track.Track] = [
                track for track in self.session.tracks if not track.is_audacity_project
            ]
            self.average_bpm = self.session.bpm
        else:
            # Audacity track group
            track = self.session.track_for_name(self.name)
            self.tracks = [track]
            self.average_bpm = track.average_bpm

    def create_metronome(self) -> Optional[manokee.metronome.Metronome]:
        if self.name == "":
            return manokee.metronome.Metronome(
                bpm=self.session.bpm,
                time_signature=self.session.time_signature,
                frame_rate=self.session.frame_rate,
            )
        else:
            return None
