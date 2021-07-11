from pathlib import Path

from manokee.session import Session
import pytest


def test_load_session():
    # TODO Make it possible to open a session without specifying frame rate
    session = Session(48000, "tests/assets/sessions/simple/session.mnk")
    assert session.session_directory == Path("tests/assets/sessions/simple/")
    assert session.files_in_session_directory() == {
        Path("tests/assets/sessions/simple/session.mnk"),
        Path("tests/assets/sessions/simple/some-file.txt"),
        Path("tests/assets/sessions/simple/video/file.txt"),
    }
    assert session.bpm == 154
    assert sum(1 for _ in session.tracks) == 2
    assert sum(1 for _ in session.marks) == 0


@pytest.mark.skip(reason="Not implemented yet")
def test_create_session():
    # TODO Make it possible to open a session without specifying frame rate
    session = Session(48000, "tests/assets/nonexistent.mnk")
    assert sum(1 for _ in session.tracks) == 0
