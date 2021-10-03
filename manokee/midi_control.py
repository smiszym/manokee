import logging
import manokee.application
import mido
import threading
from time import sleep
from typing import Callable, Optional


class MidiInputReceiver(threading.Thread):
    def __init__(self, input_callback: Callable[[mido.Message], None]):
        super(MidiInputReceiver, self).__init__()
        self._should_stop = threading.Event()
        self._input_callback = input_callback

    def run(self):
        available_ports = [
            port for port in mido.get_input_names() if "Midi Through" not in port
        ]
        if len(available_ports) < 1:
            return
        with mido.open_input(available_ports[0]) as port:
            logging.info(f"Using {port}")
            while not self._should_stop.is_set():
                for message in port.iter_pending():
                    self._input_callback(message)
                sleep(0)

    def stop(self):
        self._should_stop.set()
        self.join()


class ManokeeMidiMessage:
    def apply(self, application: "manokee.application.Application"):
        raise NotImplementedError


class VolumeChangeMessage(ManokeeMidiMessage):
    def __init__(self, track_number: int, new_value: float):
        self.track_number = track_number
        self.new_value = new_value

    def apply(self, application: "manokee.application.Application"):
        session = application.session
        if session is not None:
            track = list(session.tracks)[self.track_number]
            track.fader.vol_dB = self.new_value
            session._notify_observers()


class ButtonMessage(ManokeeMidiMessage):
    def __init__(self, track_number: int, action: int):
        self.track_number = track_number
        self.action = action

    def apply(self, application: "manokee.application.Application"):
        session = application.session
        if session is not None:
            track = list(session.tracks)[self.track_number]
            if self.action == 0:
                track.is_rec = not track.is_rec
                session._notify_observers()
            elif self.action == 1:
                track.is_mute = not track.is_mute
                session._notify_observers()
            elif self.action == 2:
                track.is_solo = not track.is_solo
                session._notify_observers()


class StartRecordingMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        application.start_recording()


class StartMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        application.play_stop()


class StopMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        application.play_stop()


class RewindMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        pass


class FastForwardMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        pass


class GoToBeginningMessage(ManokeeMidiMessage):
    def apply(self, application: "manokee.application.Application"):
        application.amio_interface.set_position(0)


class MidiInterpreter:
    first_track_vol_control = 3
    last_track_vol_control = 10
    master_vol_control = 11

    first_track_button_control = 23
    last_track_button_control = 30
    master_button_control = 31

    def __init__(self):
        self.bank = None  # unknown until we get the first update

    def interpret(self, raw_message: mido.Message) -> Optional[ManokeeMidiMessage]:
        if raw_message.type == "control_change":
            if (
                self.first_track_vol_control
                <= raw_message.control
                <= self.last_track_vol_control
            ):
                return VolumeChangeMessage(
                    raw_message.control - self.first_track_vol_control,
                    raw_message.value * 30 / 127 - 20,
                )
            elif (
                self.first_track_button_control
                <= raw_message.control
                <= self.last_track_button_control
                and raw_message.value == 0
            ):
                return ButtonMessage(
                    raw_message.control - self.first_track_button_control, self.bank
                )
            elif raw_message.control == 44 and raw_message.value == 0:
                return StartRecordingMessage()
            elif raw_message.control == 45 and raw_message.value == 0:
                return StartMessage()
            elif raw_message.control == 46 and raw_message.value == 0:
                return StopMessage()
            elif raw_message.control == 47 and raw_message.value == 0:
                return RewindMessage()
            elif raw_message.control == 48 and raw_message.value == 0:
                return FastForwardMessage()
            elif raw_message.control == 49 and raw_message.value == 0:
                return GoToBeginningMessage()
        elif raw_message.type == "sysex":
            if raw_message.data[:8] == (66, 64, 0, 1, 4, 0, 95, 79):
                self.bank = raw_message.data[8]
        return None
