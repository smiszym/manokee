import os
from typing import List, Optional

from amio import AudioClip
from xml.etree.ElementTree import Element, ElementTree


class LabelTrack:
    def __init__(self, element: Element, ns):
        self.element = element
        self.ns = ns

    def get_name(self):
        return self.element.attrib["name"]

    def get_label_positions(self):
        return (
            float(label.attrib["t"])
            for label in self.element.findall("ns:label", self.ns)
        )


class WaveBlock:
    def __init__(self, element: Element, ns):
        self.element = element
        self.ns = ns

    def get_start(self):
        return self.element.attrib["start"]

    def get_file_element(self):
        return self.element.find("ns:simpleblockfile", self.ns)

    def get_filename(self):
        return self.get_file_element().attrib["filename"]

    def get_len(self):
        return int(self.get_file_element().attrib["len"])


class WaveClip:
    def __init__(self, element: Element, ns, project):
        self.element = element
        self.ns = ns
        self.project = project

    def get_offset(self):
        return float(self.element.attrib["offset"])

    def get_wave_blocks(self):
        return (
            WaveBlock(block, self.ns)
            for block in self.element.find("ns:sequence", self.ns).findall(
                "ns:waveblock", self.ns
            )
        )

    def get_audio_clips(self):
        return (
            AudioClip.from_au_file(
                self.project.get_blockfile_path(block.get_filename())
            )
            for block in self.get_wave_blocks()
        )

    def as_audio_clip(self):
        return AudioClip.concatenate(self.get_audio_clips())


class WaveTrack:
    def __init__(self, element: Element, ns, project):
        self.element = element
        self.ns = ns
        self.project = project

    def get_name(self):
        return self.element.attrib["name"]

    def get_channel(self):
        return self.element.attrib["channel"]

    def get_rate(self):
        return float(self.element.attrib["rate"])

    def get_clips(self):
        return (
            WaveClip(clip, self.ns, self.project)
            for clip in self.element.findall("ns:waveclip", self.ns)
        )

    def as_audio_clip(self):
        # TODO Support offsets etc.
        clip = next(self.get_clips()).as_audio_clip()
        clip.frame_rate = self.get_rate()
        return clip


class AudacityProject(ElementTree):
    def __init__(self, aup_file_path):
        super(AudacityProject, self).__init__()
        self.ns = {"ns": "http://audacity.sourceforge.net/xml/"}
        self.aup_file_path = os.path.join(os.path.curdir, aup_file_path)

    def get_label_track(self, name: Optional[str] = None):
        root = self.getroot()
        label_tracks = [
            LabelTrack(track, self.ns)
            for track in root.findall("ns:labeltrack", self.ns)
        ]
        if name is None:
            return label_tracks[0]
        else:
            return next(track for track in label_tracks if track.get_name() == name)

    def get_wave_tracks(self):
        root = self.getroot()
        return (
            WaveTrack(track, self.ns, self)
            for track in root.findall("ns:wavetrack", self.ns)
        )

    def multichannel_track_by_name(self, name: str) -> List[WaveTrack]:
        return [track for track in self.get_wave_tracks() if track.get_name() == name]

    def get_project_dir(self):
        return os.path.dirname(self.aup_file_path)

    def get_blockfile_path(self, name):
        return os.path.join(
            self.get_project_dir(),
            self.getroot().attrib["projname"],
            name[0:3],
            "d" + name[3:5],
            name,
        )

    def as_audio_clip(self, track: Optional[str]):
        if track is None:
            # use the first track as the default
            track = next(self.get_wave_tracks()).get_name()
        wave_tracks = self.multichannel_track_by_name(track)
        if len(wave_tracks) == 1:
            return wave_tracks[0].as_audio_clip()
        elif len(wave_tracks) == 2:
            left = wave_tracks[0].as_audio_clip()
            right = wave_tracks[1].as_audio_clip()
            return AudioClip.stereo_clip_from_mono_clips(left, right)
        else:
            ValueError(
                f"Unsupported number of channels in Audacity track {track}: "
                f"{len(wave_tracks)}"
            )


def parse(source, parser=None):
    result = AudacityProject(source)
    result.parse(source, parser)
    return result
