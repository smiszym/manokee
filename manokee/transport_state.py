from enum import Enum


class TransportState(Enum):
    STOPPED = 0
    ROLLING = 1
    RECORDING = 2

    def __str__(self):
        return self.name.lower()
