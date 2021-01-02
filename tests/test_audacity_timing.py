from unittest.mock import Mock

from manokee.timing.audacity_timing import AudacityTiming


def test_audacity_timing():
    label_track = Mock()
    label_track.get_name = Mock(return_value="ofs=0")
    label_track.get_label_positions = Mock(return_value=[1.0, 3.0, 5.0])
    project = Mock()
    project.get_label_track = Mock(return_value=label_track)
    timing = AudacityTiming(project)

    assert timing.seconds_to_beat(-1.0) == -1
    assert timing.seconds_to_beat(1.0) == 0
    assert timing.seconds_to_beat(3.0) == 1
    assert timing.seconds_to_beat(5.0) == 2
    assert timing.seconds_to_beat(7.0) == 3

    assert timing.beat_to_seconds(-1) == -1.0
    assert timing.beat_to_seconds(0) == 1.0
    assert timing.beat_to_seconds(1) == 3.0
    assert timing.beat_to_seconds(2) == 5.0
    assert timing.beat_to_seconds(3) == 7.0
    assert timing.beat_to_seconds(4) == 9.0
