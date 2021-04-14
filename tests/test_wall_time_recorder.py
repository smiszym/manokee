from datetime import datetime, timedelta

from manokee.wall_time_recorder import WallTimeEntry, WallTimeRecorder


def test_basic_1():
    recorder = WallTimeRecorder()
    recorder.add(
        timedelta(minutes=0), datetime(2021, 1, 1, 13, 0), timedelta(minutes=3)
    )
    recorder.add(
        timedelta(minutes=1), datetime(2021, 1, 1, 20, 0), timedelta(minutes=1)
    )
    assert recorder.entries == [
        WallTimeEntry(
            timedelta(minutes=0), datetime(2021, 1, 1, 13, 0), timedelta(minutes=1)
        ),
        WallTimeEntry(
            timedelta(minutes=1), datetime(2021, 1, 1, 20, 0), timedelta(minutes=1)
        ),
        WallTimeEntry(
            timedelta(minutes=2), datetime(2021, 1, 1, 13, 2), timedelta(minutes=1)
        ),
    ]


def test_basic_2():
    recorder = WallTimeRecorder()
    recorder.add(
        timedelta(minutes=1), datetime(2021, 1, 1, 13, 0), timedelta(minutes=1)
    )
    recorder.add(
        timedelta(minutes=0), datetime(2021, 1, 1, 20, 0), timedelta(minutes=3)
    )
    assert recorder.entries == [
        WallTimeEntry(
            timedelta(minutes=0), datetime(2021, 1, 1, 20, 0), timedelta(minutes=3)
        ),
    ]


def test_negative_session_time():
    recorder = WallTimeRecorder()
    recorder.add(
        timedelta(seconds=-1), datetime(2021, 1, 1, 13, 0, 0), timedelta(seconds=30)
    )
    assert recorder.entries == [
        WallTimeEntry(
            timedelta(0), datetime(2021, 1, 1, 13, 0, 1), timedelta(seconds=29)
        ),
    ]
