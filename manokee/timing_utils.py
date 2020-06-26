def frame_to_beat_number(amio_interface, timing, frame):
    return timing.seconds_to_beat(amio_interface.frame_to_secs(frame))


def beat_number_to_frame(amio_interface, timing, beat_number):
    return amio_interface.secs_to_frame(timing.beat_to_seconds(beat_number))


def frame_to_bar_beat(amio_interface, session, timing, frame):
    if session is None:
        return None, None
    absolute_beat = int(
        timing.seconds_to_beat(amio_interface.frame_to_secs(frame)))
    sig = session.time_signature
    return absolute_beat // sig, absolute_beat % sig
