import amio
from manokee.time_formatting import format_frame, parse_frame


def test_format_frame():
    interface = amio.create_io_interface("dummy", frame_rate=48000)
    assert format_frame(interface, 0) == "0:00.0"
    assert format_frame(interface, 48000) == "0:01.0"
    assert format_frame(interface, 96000) == "0:02.0"
    assert format_frame(interface, 72000) == "0:01.5"
    assert format_frame(interface, 2880000) == "1:00.0"
    assert format_frame(interface, 28800000) == "10:00.0"
    assert format_frame(interface, 288000000) == "100:00.0"


def test_parse_frame():
    interface = amio.create_io_interface("dummy", frame_rate=48000)
    assert parse_frame(interface, "0:00.0") == 0
    assert parse_frame(interface, "0:01.0") == 48000
    assert parse_frame(interface, "0:02.0") == 96000
    assert parse_frame(interface, "0:01.5") == 72000
    assert parse_frame(interface, "1:00.0") == 2880000
    assert parse_frame(interface, "10:00.0") == 28800000
    assert parse_frame(interface, "100:00.0") == 288000000
