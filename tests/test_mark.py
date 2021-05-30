import pytest

from manokee.mark import Mark


def test_from_str():
    assert Mark.from_str("beat 0").beat == 0
    assert Mark.from_str("beat 5").beat == 5
    assert Mark.from_str("beat 2034").beat == 2034


def test_to_str():
    assert str(Mark(beat=0)) == "beat 0"
    assert str(Mark(beat=3)) == "beat 3"
    assert str(Mark(beat=1645)) == "beat 1645"


@pytest.mark.parametrize("s", ("abc", "beat a", "beat"))
def test_from_str__invalid(s):
    with pytest.raises(ValueError):
        Mark.from_str(s)
