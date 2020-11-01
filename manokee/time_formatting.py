from amio import Interface
import re
from typing import Optional


def format_seconds(seconds: float) -> str:
    full_seconds = int(seconds)
    minutes = full_seconds // 60
    full_seconds = full_seconds % 60
    tenths = int(seconds * 10) % 10
    return f"{minutes}:{full_seconds:02d}.{tenths}"


def format_frame(amio_interface: Interface, frame: int) -> str:
    if amio_interface is None:
        return f"frame {frame}"
    return format_seconds(amio_interface.frame_to_secs(frame))


time_format_pattern = re.compile(r"\s*([0-9]+):([0-9]+)\.([0-9])\s*")


def parse_seconds(formatted: str) -> Optional[float]:
    m = time_format_pattern.match(formatted)
    if m is None:
        return None
    min = int(m.group(1))
    sec = int(m.group(2))
    tenths = int(m.group(3))
    return 60 * min + sec + 0.1 * tenths


def parse_frame(amio_interface: Interface, formatted: str) -> Optional[int]:
    if amio_interface is None:
        return None
    return amio_interface.secs_to_frame(parse_seconds(formatted))


def format_beat(bar: int, beat: int) -> str:
    if bar is None or beat is None:
        return "??+??"
    else:
        return f"{bar + 1}+{beat + 1}"
