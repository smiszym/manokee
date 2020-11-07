from amio import AudioClip, Fader, PlayspecEntry
import manokee.metronome
import manokee.session
import manokee.track
from typing import Iterable, Generator, Optional

PlayspecEntryGenerator = Generator[PlayspecEntry, None, None]


def track_playspec_entries(
    tracks: Iterable["manokee.track.Track"],
) -> PlayspecEntryGenerator:
    tracks = list(tracks)
    is_soloed = any(track.is_solo for track in tracks)
    additional_data = {
        track: {"audible": track.is_solo if is_soloed else not track.is_mute}
        for track in tracks
    }
    for track in tracks:
        clip = track.get_audio_clip()
        if clip is not None:
            if additional_data[track]["audible"]:
                fader = track.fader
            else:
                fader = Fader(float("-inf"))
            yield PlayspecEntry(
                clip,
                0,
                len(clip),
                0,
                0,
                fader.left_gain_factor,
                fader.right_gain_factor,
            )


def metronome_playspec_entries(
    session: "manokee.session.Session",
    metronome: Optional["manokee.metronome.Metronome"],
) -> PlayspecEntryGenerator:
    if not metronome:
        return
    metronome_fader = Fader(
        float(session.configuration["metronome_vol"]),
        float(session.configuration["metronome_pan"]),
    )
    if session.configuration["metronome"] == "1":
        metronome_clip = metronome.audio_clip
        yield PlayspecEntry(
            metronome_clip,
            0,
            len(metronome_clip),
            0,
            len(metronome_clip),
            metronome_fader.left_gain_factor,
            metronome_fader.right_gain_factor,
        )
