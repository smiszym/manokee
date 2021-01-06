import amio
from manokee.global_config import *
from manokee.input_recorder import InputFragment, InputRecorder
from manokee.meter import Meter
from manokee.midi_control import ManokeeMidiMessage, MidiInputReceiver, MidiInterpreter
from manokee.playspec_controller import PlayspecController
from manokee.session_holder import SessionHolder
from manokee.workspace import Workspace
from typing import List, Optional


class Application:
    """
    Manokee application. This class implements functionality that
    the web interface provides.
    """

    def __init__(self):
        self._session_holder = SessionHolder()
        self._amio_interface = None
        # TODO Make it possible to open a session without specifying frame rate
        self._session_holder.session = Session(
            self._amio_interface.get_frame_rate()
            if self._amio_interface is not None
            else 48000
        )
        self._playspec_controller = None
        self._auto_rewind = False
        self._auto_rewind_position = 0
        self.on_session_change = None
        self._global_config = read_global_config()
        self._workspace = Workspace(self._global_config.get("workspace"))
        self._recent_sessions = RecentSessions()
        self._input_recorder = InputRecorder(4, 2)
        self._midi_interpreter = MidiInterpreter()
        self._midi_input_receiver = MidiInputReceiver(
            lambda raw_message: self._on_midi_message(
                self._midi_interpreter.interpret(raw_message)
            )
        )
        self._midi_input_receiver.start()

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
        self._recent_sessions.append(
            self._playspec_controller.session.session_file_path
        )
        if self.on_session_change is not None:
            self.on_session_change()

    def start_audio_io(self):
        assert self._amio_interface is None
        self._amio_interface = amio.create_io_interface()
        self._amio_interface.init("manokee")
        self._amio_interface.input_chunk_callback = self._on_input_chunk
        self._playspec_controller = PlayspecController(
            self.amio_interface, self._session_holder
        )
        self._playspec_controller.on_session_change = self._onSessionChanged
        self._recent_sessions.read()

    def stop_audio_io(self):
        assert self._amio_interface is not None
        self._amio_interface.close()
        self._amio_interface = None
        self._recent_sessions.write()

    def save_session_as(self, name: str):
        path = self._workspace.session_file_path_for_session_name(name)
        self._playspec_controller.session.session_file_path = path
        self._playspec_controller.session.save()

    def play_stop(self):
        was_rolling = self._amio_interface.is_transport_rolling()
        if not was_rolling:
            self._auto_rewind_position = self._amio_interface.get_position()
        self._amio_interface.set_transport_rolling(not was_rolling)
        if self._auto_rewind and was_rolling:
            self._amio_interface.set_position(self._auto_rewind_position)

    def start_recording(self):
        if self._amio_interface.is_transport_rolling():
            return
        self._auto_rewind_position = self._amio_interface.get_position()
        self._input_recorder.is_recording = True
        self._amio_interface.set_transport_rolling(True)

    def commit_recording(self, fragment_id: int):
        fragment = self._input_recorder.fragment_by_id(fragment_id)
        clip = fragment.as_clip()
        left = clip.channel(0)
        right = clip.channel(1)
        session = self._playspec_controller.session
        for track in session.tracks:
            if track.is_rec:
                clip_to_commit = left if track.rec_source == "L" else right
                clip = track.get_audio_clip()
                clip.writeable = True
                clip.overwrite(
                    clip_to_commit, fragment.starting_frame, extend_to_fit=True
                )
                clip.writeable = False
                track.requires_audio_save = True
                track.notify_modified()

    def _on_input_chunk(self, input_chunk: amio.InputAudioChunk):
        self._input_recorder.append_input_chunk(input_chunk)
        self._input_recorder.remove_old_fragments(self._amio_interface)
