import asyncio
import logging
from typing import Set

from aiohttp import web
import jsonpatch
import psutil

from manokee.application import Application
from manokee.looping import LoopFragment
from manokee.ping import Ping
from manokee.session import Session
from manokee.time_formatting import format_beat, format_frame
from manokee.timing_utils import beat_number_to_frame
import socketio


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("engineio").setLevel(logging.WARNING)
logging.getLogger("socketio").setLevel(logging.WARNING)
logging.getLogger("webserver").setLevel(logging.WARNING)

routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    return web.FileResponse("manokee/web/front/dist/index.html")


@routes.get("/bundle.js")
async def bundle(request):
    return web.FileResponse("manokee/web/front/dist/bundle.js")


@routes.get("/favicon.ico")
async def favicon(request):
    return web.FileResponse("manokee/web/front/dist/favicon.svg")


@routes.get("/main.css")
async def main_css(request):
    return web.FileResponse("manokee/web/front/dist/main.css")


@routes.get("/A.svg")
async def A(request):
    return web.FileResponse("manokee/web/front/dist/A.svg")


@routes.get("/B.svg")
async def B(request):
    return web.FileResponse("manokee/web/front/dist/B.svg")


@routes.get("/more.svg")
async def more(request):
    return web.FileResponse("manokee/web/front/dist/more.svg")


@routes.get("/play-pause.svg")
async def play_pause(request):
    return web.FileResponse("manokee/web/front/dist/play-pause.svg")


@routes.get("/record.svg")
async def record(request):
    return web.FileResponse("manokee/web/front/dist/record.svg")


@routes.get("/commit.svg")
async def commit(request):
    return web.FileResponse("manokee/web/front/dist/commit.svg")


@routes.get("/discard.svg")
async def discard(request):
    return web.FileResponse("manokee/web/front/dist/discard.svg")


@routes.get("/remove-arm-for-recording.svg")
async def remove_arm_for_recording(request):
    return web.FileResponse("manokee/web/front/dist/remove-arm-for-recording.svg")


@routes.get("/rewind.svg")
async def rewind(request):
    return web.FileResponse("manokee/web/front/dist/rewind.svg")


@routes.get("/track-edit-mode.svg")
async def track_edit_mode(request):
    return web.FileResponse("manokee/web/front/dist/track-edit-mode.svg")


@routes.get("/audio-io-running.svg")
async def audio_io_running(request):
    return web.FileResponse("manokee/web/front/dist/audio-io-running.svg")


@routes.get("/audio-io-stopped.svg")
async def audio_io_stopped(request):
    return web.FileResponse("manokee/web/front/dist/audio-io-stopped.svg")


@routes.get("/status-good.svg")
async def status_good(request):
    return web.FileResponse("manokee/web/front/dist/status-good.svg")


@routes.get("/status-bad.svg")
async def status_bad(request):
    return web.FileResponse("manokee/web/front/dist/status-bad.svg")


@routes.get("/mark.svg")
async def mark(request):
    return web.FileResponse("manokee/web/front/dist/mark.svg")


@routes.get("/metronome.svg")
async def metronome(request):
    return web.FileResponse("manokee/web/front/dist/metronome.svg")


@routes.get("/transport.svg")
async def transport(request):
    return web.FileResponse("manokee/web/front/dist/transport.svg")


@routes.get("/microphone.svg")
async def microphone(request):
    return web.FileResponse("manokee/web/front/dist/microphone.svg")


@routes.get("/session.svg")
async def session(request):
    return web.FileResponse("manokee/web/front/dist/session.svg")


@routes.get("/auto-rewind.svg")
async def auto_rewind(request):
    return web.FileResponse("manokee/web/front/dist/auto-rewind.svg")


sio = socketio.AsyncServer(async_mode="aiohttp")
app = web.Application()
app.add_routes(routes)
sio.attach(app)

application = Application()
_process = psutil.Process()


def _construct_state_json(ping):
    amio_interface = application.amio_interface
    if amio_interface is not None:
        playspec_controller = application.playspec_controller
        frame = amio_interface.get_position()
        is_transport_rolling = amio_interface.is_transport_rolling()
        position_seconds = amio_interface.frame_to_secs(frame)
        session = application.session
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
        bar, beat = application.frame_to_bar_beat(frame + 2)
    else:
        bar, beat = None, None
    state_update_json = {
        "ping_latency": ping.current_ping_latency,
        "state_update_id": ping.ping_id_to_send(),
        "is_audio_io_running": application.is_audio_io_running,
        "frame_rate": application.frame_rate,
        "is_transport_rolling": is_transport_rolling,
        "position_seconds": position_seconds,
        "frame_formatted": format_frame(amio_interface, frame),
        "beat_formatted": format_beat(bar, beat),
        "current_bar": bar,
        "active_track_group_name": application.active_track_group_name,
        "is_looped": application.loop_spec is not None,
        "auto_rewind": application.auto_rewind,
        "session": session_js,
        "capture_meter": application.capture_meter.current_rms_dB,
        "recorded_fragments": recorded_fragments,
        "fragment_being_revised_id": application.fragment_being_revised_id,
        "process_rss": _process.memory_info().rss,
        "available_ram": psutil.virtual_memory().available,
        "track_memory_usage_mb": {
            # 3 because there are 3 copies of the audio data currently:
            # - NumPy array
            # - immutable bytes object with audio data
            # - block of memory used by the native I/O thread
            track.name: int(3 * track.get_audio_clip().memory_usage_mb)
            for track in application.session.tracks
        }
        if application.session is not None
        else {},
    }
    return state_update_json


async def _update_task(app):
    # TODO: Exceptions silently stop execution, i.e., there is no message in logs!
    try:
        while True:
            for sid in app["client_sids"]:
                async with sio.session(sid) as session:
                    prev_state = session.get("previous_state", {})
                    current_state = _construct_state_json(session["ping"])
                    patch = jsonpatch.make_patch(prev_state, current_state)
                    await sio.emit("state_update", patch.to_string())
                    session["previous_state"] = current_state
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        pass
    finally:
        logging.info("Finished background update task")


async def start_background_tasks(app):
    app["client_sids"] = set()
    app["update_task"] = asyncio.create_task(_update_task(app))


async def cleanup_background_tasks(app):
    app["update_task"].cancel()
    await app["update_task"]


app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)


@sio.event
async def connect(sid, environ):
    app["client_sids"].add(sid)
    print(f"A client connected with session ID {sid}")
    async with sio.session(sid) as session:
        session["ping"] = Ping()
    if not application.is_audio_io_running:
        await application.start_audio_io()
        await sio.emit("workspace_sessions", application.workspace.sessions)


@sio.event
def disconnect(sid):
    app["client_sids"].remove(sid)
    print(f"A client disconnected with session ID {sid}")


@sio.event
async def state_update_ack(sid, attr):
    async with sio.session(sid) as session:
        session["ping"].pong_received(attr["id"])


@sio.event
async def start_audio(sid):
    await application.start_audio_io()
    await sio.emit("workspace_sessions", application.workspace.sessions)


@sio.event
async def stop_audio(sid):
    await application.stop_audio_io()


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


async def emit_track_metering_data():
    # Due to a message limit in socketio (btw, the message exceeding
    # the limit is currently silently discarded, which I consider a bug),
    # we need to send the metering data in parts. I decided to split
    # the data per track, but for long tracks this will break
    # (long tracks may not receive any data). TODO: Fix it.
    for track in application.session.tracks:
        await sio.emit("track_metering_data", _js_metering_data_for_track(track))


@sio.event
async def load_session(sid, attr):
    if application.amio_interface is not None:
        path = attr["session"]
        logging.info("Loading session: " + path)
        application.session = Session(application.amio_interface.get_frame_rate(), path)

        for track in application.session.tracks:
            await track.load()
        await emit_track_metering_data()


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
def metronome_pan_change(sid, attr):
    application.session.change_metronome_pan(float(attr["pan"]))


@sio.event
def add_track(sid, attr):
    application.session.add_track(
        attr["name"], application.amio_interface.get_frame_rate()
    )


@sio.event
def go_to_beat(sid, attr):
    application.go_to_beat(attr["beat"])


@sio.event
def go_to_bar(sid, attr):
    application.go_to_bar(attr["bar"])


@sio.event
def go_to_mark(sid, attr):
    application.go_to_mark(attr["mark"])


@sio.event
def set_mark_at_bar(sid, attr):
    beat = application.session.bar_to_beat(attr["bar"])
    application.session.set_mark_at_beat(attr["name"], beat)


@sio.event
def play_stop(sid):
    application.play_stop()


@sio.event
def start_recording(sid):
    application.start_recording()


@sio.event
async def commit_recording(sid, attr):
    application.commit_recording(attr["fragment"])
    await emit_track_metering_data()


@sio.event
def commit_revised_fragment(sid):
    application.commit_revised_fragment()


@sio.event
def stop_revising(sid):
    application.stop_revising()


@sio.event
def set_active_track_group(sid, attr):
    name = attr["group_name"]
    logging.info(f"Setting active track group to: {name}")
    application.set_active_track_group_name(name)


@sio.event
def set_loop_spec(sid, attr):
    def bar_of(mark_or_bar):
        if isinstance(mark_or_bar, (int, float)):
            return mark_or_bar
        elif isinstance(mark_or_bar, str):
            return application.session.marks[mark_or_bar].beat

    spec = [
        LoopFragment(
            bar_of(fragment["bar_a"]),
            bar_of(fragment["bar_b"]),
            fragment["track_group_name"],
        )
        for fragment in attr["loop_spec"]
    ]
    application.set_loop_spec(spec)


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
