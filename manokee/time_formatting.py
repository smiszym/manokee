from manokee.timing_utils import frame_to_beat_number
import re


def format_frame(amio_interface, frame):
    if amio_interface is None:
        return f"frame {frame}"
    seconds = amio_interface.frame_to_secs(frame)
    full_seconds = int(seconds)
    minutes = full_seconds // 60
    full_seconds = full_seconds % 60
    tenths = int(seconds * 10) % 10
    return f"{minutes}:{full_seconds:02d}.{tenths}"


time_format_pattern = re.compile(r"\s*([0-9]+):([0-9]+)\.([0-9])\s*")


def parse_frame(amio_interface, formatted):
    if amio_interface is None:
        return
    m = time_format_pattern.match(formatted)
    if m is not None:
        min = int(m.group(1))
        sec = int(m.group(2))
        tenths = int(m.group(3))
        seconds = 60 * min + sec + 0.1 * tenths
        return amio_interface.secs_to_frame(seconds)


def format_beat(amio_interface, playspec_controller, frame):
    if amio_interface is None:
        return "??+??"
    # frame + 1, because we want to include the frame just before
    # the one that starts a beat
    beat = int(frame_to_beat_number(
        amio_interface, playspec_controller.timing, frame + 1))
    session = playspec_controller.session
    if session is None:
        return "--"
    sig = session.time_signature
    return f"{beat // sig + 1}+{beat % sig + 1}"
