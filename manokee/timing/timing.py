class Timing:
    def beat_to_seconds(self, beat_number: float) -> float:
        """
        Convert beat number to seconds.
        :param beat_number: Beat number counted from 0.
        :return: Time in seconds.
        """
        raise NotImplementedError

    def seconds_to_beat(self, time: float) -> float:
        """
        Convert seconds to beat number.
        :param time: Time in seconds.
        :return: Beat number counted from 0.
        """
        raise NotImplementedError
