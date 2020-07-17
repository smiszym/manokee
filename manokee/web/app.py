import logging
from manokee.application import Application
from manokee.session import Session
from manokee.time_formatting import format_beat, format_frame, parse_frame
from manokee.timing_utils import beat_number_to_frame
import socketio
import threading


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)


sio = socketio.Server()
app = socketio.WSGIApp(
    sio, static_files={
        '/': {
            'content_type': 'text/html',
            'filename': 'manokee/web/front/dist/index.html'},
        '/bundle.js': {
            'content_type': 'text/javascript',
            'filename': 'manokee/web/front/dist/bundle.js'},
        '/favicon.ico': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/favicon.svg'},
        '/main.css': {
            'content_type': 'text/css',
            'filename': 'manokee/web/front/dist/main.css'},
        '/A.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/A.svg'},
        '/B.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/B.svg'},
        '/more.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/more.svg'},
        '/play-pause.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/play-pause.svg'},
        '/record.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/record.svg'},
        '/remove-arm-for-recording.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/remove-arm-for-recording.svg'},
        '/rewind.svg': {
            'content_type': 'image/svg+xml',
            'filename': 'manokee/web/front/dist/rewind.svg'},
    }
)
application = Application()
_should_stop_updating_clients = threading.Event()


def _construct_state_update_json():
    amio_interface = application.amio_interface
    if amio_interface is not None:
        playspec_controller = application.playspec_controller
        frame = amio_interface.get_position()
        position_seconds = amio_interface.frame_to_secs(frame)
        session = playspec_controller.session
        session_js = session.to_js() if session is not None else {}
    else:
        frame = 0
        position_seconds = 0
        playspec_controller = None
        session_js = {}
    recorded_fragments = [fragment.to_js(amio_interface)
                          for fragment in application.recorded_fragments]
    return {'is_audio_io_running': application.is_audio_io_running,
            'frame_rate': application.frame_rate,
            'position_seconds': position_seconds,
            'frame_formatted': format_frame(amio_interface, frame),
            'beat_formatted': format_beat(
                amio_interface, playspec_controller, frame),
            'session': session_js,
            'recorded_fragments': recorded_fragments,
            }


def _update_task():
    while not _should_stop_updating_clients.wait(0.1):
        sio.emit('state_update', _construct_state_update_json())
        sio.sleep()


_update_thread = sio.start_background_task(target=_update_task)


def stop_updating_clients():
    _should_stop_updating_clients.set()
    _update_thread.join()


@sio.event
def connected(sid):
    logging.info('A client connected.')


@sio.event
def start_audio(sid):
    application.start_audio_io()
    sio.emit('recent_sessions', application.recent_sessions)


@sio.event
def stop_audio(sid):
    application.stop_audio_io()


def _js_metering_data_for_track(track):
    x, y = track.get_audio_clip().create_metering_data()
    return {'track': track.name,
            'fragment_length': x[1] - x[0],
            'values': y}


@sio.event
def load_session(sid, attr):
    path = attr['session']
    logging.info('Loading session: ' + path)
    application.playspec_controller.session = Session(path)
    # Due to a message limit in socketio (btw, the message exceeding
    # the limit is currently silently discarded, which I consider a bug),
    # we need to send the metering data in parts. I decided to split
    # the data per track, but for long tracks this will break
    # (long tracks may not receive any data). TODO: Fix it.
    for track in application.playspec_controller.session.tracks:
        sio.emit('track_metering_data',
                 _js_metering_data_for_track(track))


@sio.event
def save_session(sid):
    application.playspec_controller.session.save()


@sio.event
def toggle_metronome(sid):
    application.playspec_controller.session.toggle_metronome()


@sio.event
def metronome_vol_down(sid):
    application.playspec_controller.session.metronome_vol_down()


@sio.event
def metronome_vol_up(sid):
    application.playspec_controller.session.metronome_vol_up()


@sio.event
def add_track(sid, attr):
    application.playspec_controller.session.add_track(attr['name'])


@sio.event
def go_to_beat(sid, attr):
    frame = beat_number_to_frame(
        application.amio_interface,
        application.playspec_controller.timing,
        attr['beat'])
    application.amio_interface.set_position(frame)


@sio.event
def go_to_mark(sid, attr):
    try:
        position = application.playspec_controller.session.marks[attr['mark']]
        frame = parse_frame(application.amio_interface, position)
        application.amio_interface.set_position(frame)
    except KeyError:
        pass


@sio.event
def play_stop(sid):
    application.play_stop()


@sio.event
def start_recording(sid):
    application.start_recording()


@sio.event
def commit_recording(sid, attr):
    application.commit_recording(attr['fragment'])


@sio.event
def audacity_timing(sid, value):
    logging.info(f"Setting Audacity timing to: {str(value)}")
    application.playspec_controller.is_audacity_timing_on = value


@sio.event
def set_rec(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.is_rec = attr['enabled']


@sio.event
def set_rec_source(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.rec_source = attr['source']


@sio.event
def set_mute(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.is_mute = attr['enabled']


@sio.event
def set_solo(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.is_solo = attr['enabled']


@sio.event
def set_pan(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.fader.pan = attr['pan']
    track.notify_modified()


@sio.event
def volume_down(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.fader.vol_dB = track.fader.vol_dB - 1
    track.notify_modified()


@sio.event
def volume_up(sid, attr):
    track = application.playspec_controller.session.track_for_name(
        attr['track'])
    track.fader.vol_dB = track.fader.vol_dB + 1
    track.notify_modified()
