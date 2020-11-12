import amio
from manokee.global_config import *
from manokee.input_recorder import InputFragment, InputRecorder
from manokee.meter import Meter
from manokee.midi_control import ManokeeMidiMessage, MidiInputReceiver, MidiInterpreter
from manokee.playspec_controller import PlayspecController
from manokee.revising import Reviser
from manokee.session import Session
from manokee.session_holder import SessionHolder
from manokee.timing_utils import beat_number_to_frame
from manokee.workspace import Workspace
from typing import List, Optional, Tuple


class Application:
    """
    Manokee application. This class implements functionality that
    the web interface provides.
    """

    def __init__(self):
        self._session_holder = SessionHolder()
        self._amio_interface = None
        self._playspec_controller = None
        self._auto_rewind = False
        self._auto_rewind_position = 0
        self._global_config = read_global_config()
        self._workspace = Workspace(self._global_config.get("workspace"))
        self._recent_sessions = RecentSessions()
        self._input_recorder = InputRecorder(4, 2)
        self._reviser = Reviser(self._session_holder, self._input_recorder)
        self._midi_interpreter = MidiInterpreter()
        self._midi_input_receiver = MidiInputReceiver(
            lambda raw_message: self._on_midi_message(
                self._midi_interpreter.interpret(raw_message)
            )
        )
        self._midi_input_receiver.start()

    @property
    def session(self) -> Session:
        return self._session_holder.session

    @session.setter
    def session(self, session: Session):
        self._session_holder.session = session

    @property
    def amio_interface(self) -> amio.Interface:
        return self._amio_interface

    @property
    def is_audio_io_running(self) -> bool:
        return self._amio_interface is not None

    @property
    def frame_rate(self) -> Optional[float]:
        if self._amio_interface is not None:
            return self._amio_interface.get_frame_rate()
        return None

    @property
    def playspec_controller(self) -> PlayspecController:
        return self._playspec_controller

    @property
    def workspace(self) -> Workspace:
        return self._workspace

    @property
    def recent_sessions(self) -> List[str]:
        return self._recent_sessions.get()

    @property
    def recorded_fragments(self) -> List[InputFragment]:
        return self._input_recorder.fragments

    @property
    def capture_meter(self) -> Meter:
        return self._input_recorder.meter

    @property
    def auto_rewind(self) -> bool:
        return self._auto_rewind

    @auto_rewind.setter
    def auto_rewind(self, value: bool):
        self._auto_rewind = value

    def _on_midi_message(self, message: ManokeeMidiMessage):
        if message is not None:
            message.apply(self)

    def _onSessionChanged(self):
        session = self._session_holder.session
        if session is not None:
            self._recent_sessions.append(session.session_file_path)

    def start_audio_io(self):
        assert self._amio_interface is None
        self._amio_interface = amio.create_io_interface()
        self._amio_interface.init("manokee")
        self._playspec_controller = PlayspecController(
            self.amio_interface, self._session_holder, self._reviser
        )
        self._amio_interface.input_chunk_callback = self._on_input_chunk
        self._session_holder.session = Session(self._amio_interface.get_frame_rate())
        self._session_holder.add_observer(self._onSessionChanged)
        self._recent_sessions.read()

    def stop_audio_io(self):
        assert self._amio_interface is not None
        self._playspec_controller.close()
        self._playspec_controller = None
        self._session_holder.session = None
        self._amio_interface.close()
        self._amio_interface = None
        self._recent_sessions.write()

    def save_session_as(self, name: str):
        path = self._workspace.session_file_path_for_session_name(name)
        self._session_holder.session.session_file_path = path
        self._session_holder.session.save()

    def play_stop(self):
        was_rolling = self._amio_interface.is_transport_rolling()
        if not was_rolling:
            self._auto_rewind_position = self._amio_interface.get_position()
        self._amio_interface.set_transport_rolling(not was_rolling)
        if self._auto_rewind and was_rolling:
            self._amio_interface.set_position(self._auto_rewind_position)
        self._playspec_controller.is_recording = False

    def start_recording(self):
        if self._amio_interface.is_transport_rolling():
            return
        if not self._playspec_controller.plays_main_track_group():
            return
        if self._input_recorder.fragment_being_revised is not None:
            return
        self._auto_rewind_position = self._amio_interface.get_position()
        self._input_recorder.is_recording = True
        self._playspec_controller.is_recording = True
        self._amio_interface.set_transport_rolling(True)

    @property
    def is_revising(self) -> bool:
        return self._input_recorder.fragment_being_revised is not None

    @property
    def fragment_being_revised_id(self) -> Optional[int]:
        if self.is_revising:
            return self._input_recorder.fragment_being_revised.id
        else:
            return None

    def commit_revised_fragment(self):
        if not self.is_revising:
            return
        self.commit_recording(self._input_recorder.fragment_being_revised.id)
        self._input_recorder.fragment_being_revised = None

    def stop_revising(self):
        self._input_recorder.fragment_being_revised = None

    def commit_recording(self, fragment_id: int):
        fragment = self._input_recorder.fragment_by_id(fragment_id)
        for track in self._session_holder.session.tracks:
            if track.is_rec:
                track.commit_input_fragment_if_needed(fragment)

    def go_to_beat(self, beat: int):
        self.go_to_frame_if_possible(
            beat_number_to_frame(
                self._amio_interface, self._playspec_controller.timing, beat
            )
        )

    def go_to_bar(self, bar: int):
        session = self._session_holder.session
        if session is None:
            return
        self.go_to_frame_if_possible(
            beat_number_to_frame(
                self._amio_interface,
                self._playspec_controller.timing,
                session.time_signature * bar,
            )
        )

    def go_to_mark(self, mark_name: str):
        try:
            seconds = self._session_holder.session.mark_position_seconds(
                mark_name, self._playspec_controller.timing
            )
        except KeyError:
            return
        self.go_to_frame_if_possible(self._amio_interface.secs_to_frame(seconds))

    def go_to_frame_if_possible(self, frame: int):
        if not self._input_recorder.is_recording:
            self._amio_interface.set_position(frame)

    def set_active_track_group_name(self, name: str):
        if not self._input_recorder.is_recording:
            self._playspec_controller.set_active_track_group_name(name)

    def set_loop_spec(self, loop_spec):
        if not self._input_recorder.is_recording:
            self._playspec_controller.set_loop_spec(loop_spec)

    def frame_to_bar_beat(self, frame: int) -> Tuple[Optional[int], Optional[int]]:
        session = self._session_holder.session
        timing = self._playspec_controller.timing
        if session is None:
            return None, None
        absolute_beat = int(
            timing.seconds_to_beat(self._amio_interface.frame_to_secs(frame))
        )
        sig = session.time_signature
        return absolute_beat // sig, absolute_beat % sig

    def _on_input_chunk(self, input_chunk: amio.InputAudioChunk):
        self._input_recorder.append_input_chunk(input_chunk)
        self._input_recorder.remove_old_fragments(self._amio_interface)
        self._playspec_controller.on_input_chunk()
