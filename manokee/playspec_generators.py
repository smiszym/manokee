from amio import Fader, PlayspecEntry
import manokee.metronome
import manokee.revising
import manokee.session
import manokee.track
from typing import Dict, Generator, Iterable, Optional

PlayspecEntryGenerator = Generator[PlayspecEntry, None, None]


def track_playspec_entries(
    tracks: Iterable["manokee.track.Track"],
    audio_substitutes: Dict["manokee.track.Track", "manokee.revising.AudioSubstitute"],
) -> PlayspecEntryGenerator:
    for track in tracks:
        clip = track.audio
        substitute = audio_substitutes.get(track)
        if substitute is not None:
            start = substitute.starting_frame
            end = substitute.starting_frame + len(substitute.clip)
            yield PlayspecEntry(
                clip,
                0,
                start,
                0,
                0,
                track.fader.left_gain_factor,
                track.fader.right_gain_factor,
            )
            yield PlayspecEntry(
                substitute.clip,
                0,
                end - start,
                start,
                0,
                track.fader.left_gain_factor,
                track.fader.right_gain_factor,
            )
            yield PlayspecEntry(
                clip,
                end,
                len(clip) - end,
                end,
                0,
                track.fader.left_gain_factor,
                track.fader.right_gain_factor,
            )
        else:
            if clip is not None:
                yield PlayspecEntry(
                    clip,
                    0,
                    len(clip),
                    0,
                    0,
                    track.fader.left_gain_factor,
                    track.fader.right_gain_factor,
                )


def metronome_playspec_entries(
    session: "manokee.session.Session",
    metronome: Optional["manokee.metronome.Metronome"],
) -> PlayspecEntryGenerator:
    if not metronome:
        return
    metronome_fader = session.metronome_fader
    if session.metronome_enabled:
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
