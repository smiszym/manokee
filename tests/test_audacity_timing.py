from math import isclose

from manokee.audacity.project import parse as parse_aup
from manokee.timing.audacity_timing import AudacityTiming


def test_audacity_timing():
    project = parse_aup("tests/assets/audacity-projects/simple.aup")
    timing = AudacityTiming(project)

    assert timing.average_beat_length == 2.375

    offset = 0.1

    assert timing.beat_to_seconds(-2) == -3.75 - offset
    assert timing.beat_to_seconds(-1) == -1.375 - offset
    assert timing.beat_to_seconds(0) == 1 - offset
    assert timing.beat_to_seconds(1) == 3 - offset
    assert timing.beat_to_seconds(2) == 5 - offset
    assert timing.beat_to_seconds(3) == 7.5 - offset
    assert timing.beat_to_seconds(4) == 10 - offset
    assert timing.beat_to_seconds(9) == 22.375 - offset
    assert timing.beat_to_seconds(10) == 24.75 - offset

    # TODO: Extrapolate in seconds_to_beat
    # assert timing.seconds_to_beat(-3.75 - offset) == -2
    # assert timing.seconds_to_beat(-1.375 - offset) == -1
    assert timing.seconds_to_beat(1 - offset) == 0
    assert timing.seconds_to_beat(3 - offset) == 1
    assert timing.seconds_to_beat(5 - offset) == 2
    assert timing.seconds_to_beat(7.5 - offset) == 3
    assert timing.seconds_to_beat(10 - offset) == 4
    # assert timing.seconds_to_beat(22.375 - offset) == 9
    # assert timing.seconds_to_beat(24.75 - offset) == 10


def test_audacity_timing_beats_in_audacity_beat():
    project = parse_aup("tests/assets/audacity-projects/simple.aup")
    timing = AudacityTiming(project, beats_in_audacity_beat=2)

    assert timing.average_beat_length == 2.375 / 2

    offset = 0.1

    assert timing.beat_to_seconds(-4) == -3.75 - offset
    assert timing.beat_to_seconds(-2) == -1.375 - offset
    assert timing.beat_to_seconds(0) == 1 - offset
    assert timing.beat_to_seconds(2) == 3 - offset
    assert timing.beat_to_seconds(4) == 5 - offset
    assert timing.beat_to_seconds(6) == 7.5 - offset
    assert timing.beat_to_seconds(8) == 10 - offset
    assert timing.beat_to_seconds(18) == 22.375 - offset
    assert timing.beat_to_seconds(20) == 24.75 - offset

    # TODO: Extrapolate in seconds_to_beat
    # assert timing.seconds_to_beat(-3.75 - offset) == -4
    # assert timing.seconds_to_beat(-1.375 - offset) == -2
    assert timing.seconds_to_beat(1 - offset) == 0
    assert timing.seconds_to_beat(3 - offset) == 2
    assert timing.seconds_to_beat(5 - offset) == 4
    assert timing.seconds_to_beat(7.5 - offset) == 6
    assert timing.seconds_to_beat(10 - offset) == 8
    # assert timing.seconds_to_beat(22.375 - offset) == 18
    # assert timing.seconds_to_beat(24.75 - offset) == 20

    assert isclose(timing.beat_to_seconds(-3), -2.5625 - offset)
    assert isclose(timing.beat_to_seconds(-1), -0.1875 - offset)
    assert isclose(timing.beat_to_seconds(1), 2 - offset)
    assert isclose(timing.beat_to_seconds(3), 4 - offset)
    assert isclose(timing.beat_to_seconds(5), 6.25 - offset)
    assert isclose(timing.beat_to_seconds(7), 8.75 - offset)
    assert isclose(timing.beat_to_seconds(19), 23.5625 - offset)

    # TODO: Extrapolate in seconds_to_beat
    # assert isclose(timing.seconds_to_beat(-2.5625 - offset), -3)
    # assert isclose(timing.seconds_to_beat(-0.1875 - offset), -1)
    assert isclose(timing.seconds_to_beat(2 - offset), 1)
    assert isclose(timing.seconds_to_beat(4 - offset), 3)
    assert isclose(timing.seconds_to_beat(6.25 - offset), 5)
    assert isclose(timing.seconds_to_beat(8.75 - offset), 7)
    # assert isclose(timing.seconds_to_beat(23.5625 - offset), 19)
