import logging
from manokee.application import Application
from manokee.ping import Ping
from manokee.session import Session
from manokee.time_formatting import format_beat, format_frame, parse_frame
from manokee.timing_utils import beat_number_to_frame, frame_to_bar_beat
import socketio
import threading
import time


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("engineio").setLevel(logging.WARNING)
logging.getLogger("socketio").setLevel(logging.WARNING)
logging.getLogger("webserver").setLevel(logging.WARNING)


sio = socketio.Server()
app = socketio.WSGIApp(
    sio,
    static_files={
        "/": {
            "content_type": "text/html",
            "filename": "manokee/web/front/dist/index.html",
        },
        "/bundle.js": {
            "content_type": "text/javascript",
            "filename": "manokee/web/front/dist/bundle.js",
        },
        "/favicon.ico": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/favicon.svg",
        },
        "/main.css": {
            "content_type": "text/css",
            "filename": "manokee/web/front/dist/main.css",
        },
        "/A.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/A.svg",
        },
        "/B.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/B.svg",
        },
        "/more.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/more.svg",
        },
        "/play-pause.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/play-pause.svg",
        },
        "/record.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/record.svg",
        },
        "/remove-arm-for-recording.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/remove-arm-for-recording.svg",
        },
        "/rewind.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/rewind.svg",
        },
        "/audio-io-running.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/audio-io-running.svg",
        },
        "/audio-io-stopped.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/audio-io-stopped.svg",
        },
        "/status-good.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/status-good.svg",
        },
        "/status-bad.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/status-bad.svg",
        },
        "/mark.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/mark.svg",
        },
        "/metronome.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/metronome.svg",
        },
        "/transport.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/transport.svg",
        },
        "/microphone.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/microphone.svg",
        },
        "/session.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/session.svg",
        },
        "/auto-rewind.svg": {
            "content_type": "image/svg+xml",
            "filename": "manokee/web/front/dist/auto-rewind.svg",
        },
    },
)
application = Application()
_client_sids = set()
_ping = Ping()
_should_stop_updating_clients = threading.Event()


def _construct_state_update_json(state_update_id):
    amio_interface = application.amio_interface
    if amio_interface is not None:
        playspec_controller = application.playspec_controller
        frame = amio_interface.get_position()
        is_transport_rolling = amio_interface.is_transport_rolling()
        position_seconds = amio_interface.frame_to_secs(frame)
        session = playspec_controller.session
        session_js = session.to_js() if session is not None else {}
    else:
        frame = 0
        is_transport_rolling = False
        position_seconds = 0
        playspec_controller = None
        session_js = {}
    recorded_fragments = [
        fragment.to_js(amio_interface) for fragment in application.recorded_fragments
    ]
    if playspec_controller is not None:
        # There is a 2-frame margin so that last frames of a bar
        # are treated as the next bar. Note that these values are only
        # used in the UI, therefore such a trick is acceptable.
        bar, beat = frame_to_bar_beat(
            amio_interface,
            playspec_controller.session,
            playspec_controller.timing,
            frame + 2,
        )
    else:
        bar, beat = None, None
    state_update_json = {
        "ping_latency": _ping.current_ping_latency,
        "is_audio_io_running": application.is_audio_io_running,
        "frame_rate": application.frame_rate,
        "is_transport_rolling": is_transport_rolling,
        "position_seconds": position_seconds,
        "frame_formatted": format_frame(amio_interface, frame),
        "beat_formatted": format_beat(amio_interface, playspec_controller, frame),
        "current_bar": bar,
        "auto_rewind": application.auto_rewind,
        "session": session_js,
        "capture_meter": application.capture_meter.current_rms_dB,
        "recorded_fragments": recorded_fragments,
    }
    if state_update_id is not None:
        state_update_json["state_update_id"] = state_update_id
    return state_update_json


def _update_task():
    while not _should_stop_updating_clients.is_set():
        sio.emit("state_update", _construct_state_update_json(_ping.ping_id_to_send()))
        sio.sleep(0.05)


_update_thread = sio.start_background_task(target=_update_task)


def stop_updating_clients():
    _should_stop_updating_clients.set()
    _update_thread.join()


@sio.event
def connect(sid, environ):
    _client_sids.add(sid)
    print(f"A client connected with session ID {sid}")
    if not application.is_audio_io_running:
        application.start_audio_io()
        sio.emit("recent_sessions", application.recent_sessions)
        sio.emit("workspace_sessions", application.workspace.sessions)


@sio.event
def disconnect(sid):
    _client_sids.remove(sid)
    print(f"A client disconnected with session ID {sid}")


@sio.event
def state_update_ack(sid, attr):
    _ping.pong_received(attr["id"])


@sio.event
def start_audio(sid):
    application.start_audio_io()
    sio.emit("recent_sessions", application.recent_sessions)
    sio.emit("workspace_sessions", application.workspace.sessions)


@sio.event
def stop_audio(sid):
    application.stop_audio_io()


def _js_metering_data_for_track(track):
    clip = track.get_audio_clip()
    if clip is None:
        return {"track": track.name}
    num_fragments, rms, peak = clip.create_metering_data()
    fragment_length = len(clip) / clip.frame_rate / num_fragments
    return {
        "track": track.name,
        "fragment_length": fragment_length,
        "rms": rms.tolist(),
        "peak": peak.tolist(),
    }


@sio.event
def new_session(sid):
    if application.amio_interface is not None:
        application.session = Session(application.amio_interface.get_frame_rate())


def emit_track_metering_data():
    # Due to a message limit in socketio (btw, the message exceeding
    # the limit is currently silently discarded, which I consider a bug),
    # we need to send the metering data in parts. I decided to split
    # the data per track, but for long tracks this will break
    # (long tracks may not receive any data). TODO: Fix it.
    for track in application.session.tracks:
        sio.emit("track_metering_data", _js_metering_data_for_track(track))


@sio.event
def load_session(sid, attr):
    if application.amio_interface is not None:
        path = attr["session"]
        logging.info("Loading session: " + path)
        application.session = Session(application.amio_interface.get_frame_rate(), path)
        emit_track_metering_data()


@sio.event
def save_session(sid):
    application.session.save()


@sio.event
def save_session_as(sid, attr):
    application.save_session_as(attr["name"])


@sio.event
def toggle_metronome(sid):
    application.session.toggle_metronome()


@sio.event
def set_auto_rewind(sid, attr):
    application.auto_rewind = attr["value"]


@sio.event
def metronome_vol_down(sid):
    application.session.metronome_vol_down()


@sio.event
def metronome_vol_up(sid):
    application.session.metronome_vol_up()


@sio.event
def add_track(sid, attr):
    application.session.add_track(
        attr["name"], application.amio_interface.get_frame_rate()
    )


@sio.event
def go_to_beat(sid, attr):
    frame = beat_number_to_frame(
        application.amio_interface, application.playspec_controller.timing, attr["beat"]
    )
    application.amio_interface.set_position(frame)


@sio.event
def go_to_bar(sid, attr):
    session = application.session
    if session is None:
        return
    frame = beat_number_to_frame(
        application.amio_interface,
        application.playspec_controller.timing,
        session.time_signature * attr["bar"],
    )
    application.amio_interface.set_position(frame)


@sio.event
def go_to_mark(sid, attr):
    try:
        position = application.session.marks[attr["mark"]]
        frame = parse_frame(application.amio_interface, position)
        application.amio_interface.set_position(frame)
    except KeyError:
        pass


@sio.event
def set_mark_at_bar(sid, attr):
    amio_interface = application.amio_interface
    playspec_controller = application.playspec_controller
    beat = playspec_controller.session.bar_to_beat(attr["bar"])
    position = playspec_controller.timing.beat_to_seconds(beat)
    frame = amio_interface.secs_to_frame(position)
    frame_formatted = format_frame(amio_interface, frame)
    playspec_controller.session.marks[attr["name"]] = frame_formatted


@sio.event
def play_stop(sid):
    application.play_stop()


@sio.event
def start_recording(sid):
    application.start_recording()


@sio.event
def commit_recording(sid, attr):
    application.commit_recording(attr["fragment"])
    emit_track_metering_data()


@sio.event
def set_active_track_group(sid, attr):
    name = attr["group_name"]
    logging.info(f"Setting active track group to: {name}")
    application.playspec_controller.active_track_group_name = name


@sio.event
def unset_rec_all(sid):
    for track in application.session.tracks:
        track.is_rec = False


@sio.event
def set_rec(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.is_rec = attr["enabled"]


@sio.event
def set_rec_source(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.rec_source = attr["source"]


@sio.event
def set_mute(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.is_mute = attr["enabled"]


@sio.event
def set_solo(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.is_solo = attr["enabled"]


@sio.event
def set_pan(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.fader.pan = attr["pan"]
    track.notify_modified()


@sio.event
def volume_down(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.fader.vol_dB = track.fader.vol_dB - 1
    track.notify_modified()


@sio.event
def volume_up(sid, attr):
    track = application.session.track_for_name(attr["track"])
    track.fader.vol_dB = track.fader.vol_dB + 1
    track.notify_modified()


@sio.event
def change_tempo_by(sid, attr):
    application.session.bpm += attr["delta"]


@sio.event
def set_time_sig(sid, attr):
    application.session.time_signature = attr["time_sig"]


@sio.event
def rename_track(sid, attr):
    track = application.session.track_for_name(attr["track"])
    if track is not None:
        track.name = attr["new_name"]


@sio.event
def remove_track(sid, attr):
    application.session.remove_track(attr["track"])


@sio.event
def move_track_up(sid, attr):
    application.session.move_track_up(attr["track"])


@sio.event
def move_track_down(sid, attr):
    application.session.move_track_down(attr["track"])
