import amio
from manokee.global_config import *
from manokee.input_recorder import InputRecorder
from manokee.midi_control import MidiInputReceiver, MidiInterpreter
from manokee.playspec_controller import PlayspecController


class Application():
    """
    Manokee application. This class implements functionality that
    the web interface provides.
    """
    def __init__(self):
        self._amio_interface = None
        self._playspec_controller = None
        self._on_session_change = None
        self._global_config = read_global_config()
        self._recent_sessions = RecentSessions()
        self._input_recorder = InputRecorder(None)
        self._midi_interpreter = MidiInterpreter()
        self._midi_input_receiver = MidiInputReceiver(
            lambda raw_message: self._on_midi_message(
                self._midi_interpreter.interpret(raw_message)))
        self._midi_input_receiver.start()

    @property
    def amio_interface(self):
        return self._amio_interface

    @property
    def is_audio_io_running(self):
        return self._amio_interface is not None

    @property
    def frame_rate(self):
        if self._amio_interface is not None:
            return self._amio_interface.get_frame_rate()

    @property
    def playspec_controller(self):
        return self._playspec_controller

    @property
    def recent_sessions(self):
        return self._recent_sessions.get()

    @property
    def recorded_fragments(self):
        return self._input_recorder.fragments

    @property
    def on_session_change(self):
        return self._on_session_change

    @on_session_change.setter
    def on_session_change(self, callback):
        self._on_session_change = callback

    def _on_midi_message(self, message):
        if message is not None:
            message.apply(self)

    def _onSessionChanged(self):
        self._recent_sessions.append(
            self._playspec_controller.session.session_file_path)
        if self._on_session_change is not None:
            self._on_session_change()

    def start_audio_io(self):
        assert self._amio_interface is None
        self._amio_interface = amio.create_io_interface()
        self._amio_interface.init("manokee")
        self._amio_interface.input_chunk_callback = self._on_input_chunk
        self._playspec_controller = PlayspecController(self.amio_interface)
        self._playspec_controller.on_session_change = self._onSessionChanged
        self._input_recorder = InputRecorder(self._amio_interface)
        self._recent_sessions.read()

    def stop_audio_io(self):
        assert self._amio_interface is not None
        self._input_recorder = InputRecorder(None)
        self._amio_interface.close()
        self._amio_interface = None
        self._recent_sessions.write()

    def play_stop(self):
        self._amio_interface.set_transport_rolling(
            not self._amio_interface.is_transport_rolling())

    def start_recording(self):
        if self._amio_interface.is_transport_rolling():
            return
        self._input_recorder.is_recording = True
        self._amio_interface.set_transport_rolling(True)

    def commit_recording(self, fragment_id):
        fragment = self._input_recorder.fragment_by_id(fragment_id)
        clip = fragment.as_clip()
        left = clip.channel(0)
        right = clip.channel(1)
        session = self._playspec_controller.session
        for track in session.tracks:
            if track.is_rec:
                clip_to_commit = left if track.rec_source == 'L' else right
                track.get_audio_clip().overwrite(
                    clip_to_commit, fragment.starting_frame)
                track.notify_modified()

    def _on_input_chunk(self, input_chunk):
        self._input_recorder.append_input_chunk(input_chunk)
