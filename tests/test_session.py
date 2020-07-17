from manokee.session import Session
import pytest


def test_load_session():
    session = Session("assets/simple.mnk")
    assert session.bpm == 154
    assert sum(1 for _ in session.tracks) == 2
    assert sum(1 for _ in session.marks) == 0


@pytest.mark.skip(reason="Not implemented yet")
def test_create_session():
    session = Session("assets/nonexistent.mnk")
    assert sum(1 for _ in session.tracks) == 0
