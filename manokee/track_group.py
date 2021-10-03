import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

import manokee.metronome
import manokee.track
from manokee.audacity.project import parse as parse_aup
from manokee.timing.audacity_timing import AudacityTiming
from manokee.timing.fixed_bpm_timing import FixedBpmTiming
from manokee.timing.timing import Timing


@dataclass(eq=False)
class TrackGroup:
    name: str
    session: "manokee.session.Session"
    tracks: List[manokee.track.Track]
    timing: Timing

    @classmethod
    def from_xml(cls, session, frame_rate: float, element: ET.Element):
        timing_elements = element.find("timing")
        if timing_elements is None or len(timing_elements) != 1:
            raise ValueError("Expected exactly one element under timing XML element")
        timing_el = timing_elements[0]

        tracks_el = element.find("tracks")
        if tracks_el is None:
            raise ValueError("Expected tracks XML element")

        if timing_el.tag == "fixed-bpm-timing":
            timing: Timing = FixedBpmTiming(float(timing_el.attrib["beats-per-minute"]))
        elif timing_el.tag == "audacity-timing":
            audacity_project = parse_aup(timing_el.attrib["audacity-project"])
            beats_in_audacity_beat = int(timing_el.attrib["beats-in-audacity-beat"])
            timing = AudacityTiming(
                audacity_project, beats_in_audacity_beat=beats_in_audacity_beat
            )
        else:
            raise ValueError(f"Unknown timing type: {timing_el.tag}")
        return cls(
            name=element.attrib["name"],
            session=session,
            tracks=[
                manokee.track.Track.from_xml(
                    session=session, frame_rate=frame_rate, element=track_el
                )
                for track_el in tracks_el.findall("track")
            ],
            timing=timing,
        )

    def create_metronome(self) -> Optional[manokee.metronome.Metronome]:
        if isinstance(self.timing, FixedBpmTiming):
            return manokee.metronome.Metronome(
                bpm=60 / self.timing.average_beat_length,
                time_signature=self.session.time_signature,
                frame_rate=self.session.frame_rate,
            )
        else:
            # TODO Implement metronome for any type of timing
            return None
