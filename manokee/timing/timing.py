class Timing:
    def beat_to_seconds(self, beat_number):
        """
        Calculate when the given beat begins.
        :param beat_number: Beat number counted from 0.
        :return: Number of seconds (can be float) since the beat 0 beginning.
        """
        raise NotImplementedError

    def seconds_to_beat(self, time):
        """
        Calculate which beat is played at a given time.
        :param time: Time in seconds.
        :return: Beat number, possibly float if the given time is not exactly
        at the beginning of the beat.
        """
        raise NotImplementedError
