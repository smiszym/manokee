from pathlib import Path

import pytest

from manokee.session import Session


def test_load_session():
    # TODO Make it possible to open a session without specifying frame rate
    session = Session(48000, "tests/assets/sessions/simple/session.mnk")
    assert session.session_directory == Path("tests/assets/sessions/simple/")
    assert session.files_in_session_directory() == {
        Path("tests/assets/sessions/simple/session.mnk"),
        Path("tests/assets/sessions/simple/some-file.txt"),
        Path("tests/assets/sessions/simple/video/file.txt"),
    }
    assert session.time_signature == 4
    assert not session.metronome_enabled
    assert session.metronome_fader.vol_dB == -8.8
    assert session.metronome_fader.pan == 0
    assert len(session.marks) == 0

    assert len(session.track_groups) == 1
    main_track_group = session.track_groups[0]
    assert main_track_group.timing.bpm == 154
    assert len(main_track_group.tracks) == 2
    assert [track.filename for track in main_track_group.tracks] == [
        "./tests/assets/sessions/simple/drums_l.flac",
        "./tests/assets/sessions/simple/drums_r.flac",
    ]


@pytest.mark.skip(reason="Not implemented yet")
def test_create_session():
    # TODO Make it possible to open a session without specifying frame rate
    session = Session(48000, "tests/assets/nonexistent.mnk")
    assert sum(1 for _ in session.tracks) == 0
