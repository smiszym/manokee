from manokee.audacity.project import parse as parse_aup
from manokee.timing.audacity_timing import AudacityTiming


def test_audacity_timing():
    project = parse_aup("tests/assets/audacity-projects/simple.aup")
    timing = AudacityTiming(project)

    assert timing.average_beat_length == 2.375

    offset = 0.1

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

    assert timing.beat_to_seconds(-2) == -3.75 - offset
    assert timing.beat_to_seconds(-1) == -1.375 - offset
    assert timing.beat_to_seconds(0) == 1 - offset
    assert timing.beat_to_seconds(1) == 3 - offset
    assert timing.beat_to_seconds(2) == 5 - offset
    assert timing.beat_to_seconds(3) == 7.5 - offset
    assert timing.beat_to_seconds(4) == 10 - offset
    assert timing.beat_to_seconds(9) == 22.375 - offset
    assert timing.beat_to_seconds(10) == 24.75 - offset
