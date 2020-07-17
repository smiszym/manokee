def frame_to_beat_number(amio_interface, timing, frame):
    return timing.seconds_to_beat(amio_interface.frame_to_secs(frame))


def beat_number_to_frame(amio_interface, timing, beat_number):
    return amio_interface.secs_to_frame(timing.beat_to_seconds(beat_number))
