from manokee.ping import MovingAverage


def test_moving_average_constant():
    avg = MovingAverage(window=4)
    assert avg.get() is None
    for _ in range(20):
        assert avg.new_value(4) == 4


def test_moving_average_increasing():
    avg = MovingAverage(window=4)
    assert avg.get() is None
    assert avg.new_value(4) == 4
    assert avg.new_value(5) == 4.5
    assert avg.new_value(6) == 5
    assert avg.new_value(7) == 5.5
    assert avg.new_value(8) == 6.5
    assert avg.new_value(9) == 7.5
    assert avg.new_value(10) == 8.5


def test_moving_average_decreasing():
    avg = MovingAverage(window=4)
    assert avg.get() is None
    assert avg.new_value(4) == 4
    assert avg.new_value(3) == 3.5
    assert avg.new_value(2) == 3
    assert avg.new_value(1) == 2.5
    assert avg.new_value(0) == 1.5
    assert avg.new_value(-1) == 0.5
    assert avg.new_value(-2) == -0.5
    assert avg.new_value(-3) == -1.5


def test_moving_average_alternating():
    avg = MovingAverage(window=4)
    assert avg.get() is None
    assert avg.new_value(4) == 4
    assert avg.new_value(3) == 3.5
    assert avg.new_value(4) == (4+3+4) / 3
    assert avg.new_value(3) == 3.5
    assert avg.new_value(4) == 3.5
    assert avg.new_value(3) == 3.5
    assert avg.new_value(4) == 3.5
    assert avg.new_value(3) == 3.5
    assert avg.new_value(4) == 3.5
