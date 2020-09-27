import time
from typing import Optional


class Ping:
    timeout = 5

    def __init__(self):
        self._next_ping_id = 1
        self._sent_ping_id = None
        self._sent_ping_time = None
        self._current_ping_latency = None

    def _reset(self):
        self._sent_ping_id = None
        self._sent_ping_time = None
        self._current_ping_latency = None

    def ping_id_to_send(self) -> Optional[int]:
        if (self._sent_ping_time is not None
                and time.perf_counter() - self._sent_ping_time > self.timeout):
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
            self._current_ping_latency = (
                time.perf_counter() - self._sent_ping_time)
            self._sent_ping_id = None
            self._sent_ping_time = None
            return self._current_ping_latency

    @property
    def current_ping_latency(self) -> float:
        return self._current_ping_latency
