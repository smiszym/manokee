from collections import deque
import time
from typing import Optional


class MovingAverage:
    def __init__(self, window=30):
        self.window = window
        self.values = deque()
        self.sum = 0

    def get(self):
        l = len(self.values)
        if l == 0:
            return None
        else:
            return self.sum / l

    def new_value(self, value):
        length_before = len(self.values)
        if length_before == 0:
            self.sum = value
            self.values.append(value)
            return value

        if length_before < self.window:
            self.sum += value
        else:
            self.sum += value - self.values.popleft()
        self.values.append(value)
        return self.sum / len(self.values)


class Ping:
    timeout = 5

    def __init__(self):
        self._next_ping_id = 1
        self._sent_ping_id = None
        self._sent_ping_time = None
        self._current_ping_latency = MovingAverage()

    def _reset(self):
        self._sent_ping_id = None
        self._sent_ping_time = None
        self._current_ping_latency = MovingAverage()

    def ping_id_to_send(self) -> Optional[int]:
        if (
            self._sent_ping_time is not None
            and time.perf_counter() - self._sent_ping_time > self.timeout
        ):
            self._reset()
        if self._sent_ping_id is not None:
            return None
        id = self._next_ping_id
        self._next_ping_id += 1
        self._sent_ping_id = id
        self._sent_ping_time = time.perf_counter()
        return id

    def pong_received(self, id: int):
        if id == self._sent_ping_id:
            current = self._current_ping_latency.new_value(
                time.perf_counter() - self._sent_ping_time
            )
            self._sent_ping_id = None
            self._sent_ping_time = None
            return current

    @property
    def current_ping_latency(self) -> float:
        return self._current_ping_latency.get()
