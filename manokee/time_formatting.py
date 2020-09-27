from amio import Interface
from manokee.playspec_controller import PlayspecController
from manokee.timing_utils import frame_to_bar_beat
import re
from typing import Optional


def format_frame(amio_interface: Interface, frame: int) -> str:
    if amio_interface is None:
        return f"frame {frame}"
    seconds = amio_interface.frame_to_secs(frame)
    full_seconds = int(seconds)
    minutes = full_seconds // 60
    full_seconds = full_seconds % 60
    tenths = int(seconds * 10) % 10
    return f"{minutes}:{full_seconds:02d}.{tenths}"


time_format_pattern = re.compile(r"\s*([0-9]+):([0-9]+)\.([0-9])\s*")


def parse_frame(amio_interface: Interface, formatted: str) -> Optional[int]:
    if amio_interface is None:
        return None
    m = time_format_pattern.match(formatted)
    if m is None:
        return None
    min = int(m.group(1))
    sec = int(m.group(2))
    tenths = int(m.group(3))
    seconds = 60 * min + sec + 0.1 * tenths
    return amio_interface.secs_to_frame(seconds)


def format_beat(amio_interface: Interface,
        playspec_controller: PlayspecController, frame: int) -> str:
    if amio_interface is None:
        return "??+??"
    if playspec_controller.session is None:
        return "--"
    # frame + 1, because we want to include the frame just before
    # the one that starts a beat
    bar, beat = frame_to_bar_beat(
        amio_interface,
        playspec_controller.session,
        playspec_controller.timing,
        frame + 1)
    return f"{bar + 1}+{beat + 1}"
