import React, { Component } from 'react';
import ReactDOM from "react-dom";
import Popup from 'reactjs-popup';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import io from 'socket.io-client';

import {SummaryLine} from "./summary-line";
import {PlaybackCaptureMeters} from "./playback-capture-meters";
import {Marks} from "./marks";
import {TransportControl} from "./transport-control";
import {RecordedFragments} from "./recorded-fragments";
import {TimingManagement} from "./timing-management";
import {Tracks} from "./tracks";
import {SessionManagement} from "./session-management";
import {Status} from "./status";
import {
  factor_to_dB, calculate_tracks_audibility, gains_for_track
} from './meter-utils';

var socket;
var workspace_sessions;
var track_metering_data = {};

function renderStateUpdate(msg) {
  ReactDOM.render(
    <App
      ping_latency={msg.ping_latency}
      is_audio_io_running={msg.is_audio_io_running}
      is_transport_rolling={msg.is_transport_rolling}
      position_seconds={msg.position_seconds}
      current_position={msg.frame_formatted}
      current_beat={msg.beat_formatted}
      current_bar={msg.current_bar}
      autoRewind={msg.auto_rewind}
      session={msg.session}
      track_metering_data={track_metering_data}
      workspace_sessions={workspace_sessions}
      capture_meter={msg.capture_meter}
      recorded_fragments={msg.recorded_fragments}
      onCommit={onCommit}
      onGoToBeat={onGoToBeat}
      onGoToBar={onGoToBar}
      frame_rate={msg.frame_rate}
    />,
    document.getElementById('app')
  );
}

export function onLoad() {
    socket = io();
    socket.on('connect', function (msg) {
        socket.removeAllListeners();
        socket.emit('connected');
        socket.on('state_update', function (msg) {
            if (msg.state_update_id) {
                socket.emit('state_update_ack', {'id': msg.state_update_id});
            }
            renderStateUpdate(msg);
        });
        socket.on('workspace_sessions', function (msg) {
            workspace_sessions = msg;
        });
        socket.on('track_metering_data', function (msg) {
            track_metering_data[msg.track] = msg;
        });
    });
}

function onStartAudio() {
    socket.emit('start_audio');
}

function onStopAudio() {
    socket.emit('stop_audio');
}

function onNewSession() {
    socket.emit('new_session');
}

function onLoadSession(session_path) {
    socket.emit('load_session', {session: session_path});
}

function onSaveSession() {
    socket.emit('save_session');
}

function onSaveSessionAs(name) {
    socket.emit('save_session_as', {name: name});
}

function onToggleMetronome() {
    socket.emit('toggle_metronome');
}

function onSetAutoRewind(value) {
    socket.emit('set_auto_rewind', {value: value});
}

function onMetronomeVolDown() {
    socket.emit('metronome_vol_down');
}

function onMetronomeVolUp() {
    socket.emit('metronome_vol_up');
}

function onAddTrack(track_name) {
    socket.emit('add_track', {name: track_name});
}

function onGoToBeat(beat_number) {
    socket.emit('go_to_beat', {beat: beat_number});
}

function onGoToBar(bar_number) {
    socket.emit('go_to_bar', {bar: bar_number});
}

function onGoToMark(name) {
    socket.emit('go_to_mark', {mark: name});
}

function onSetMarkAtBar(name, bar) {
    socket.emit('set_mark_at_bar', {name: name, bar: bar});
}

function onPlayStop() {
    socket.emit('play_stop');
}

function onStartRecording() {
    socket.emit('start_recording');
}

function onCommit(fragment_id) {
    socket.emit('commit_recording', {fragment: fragment_id});
}

function onSessionTiming() {
    socket.emit('audacity_timing', false);
}

function onAudacityTiming() {
    socket.emit('audacity_timing', true);
}

function onRecChange(track_name, enabled) {
    socket.emit('set_rec', {track: track_name, enabled: enabled});
}

function onRecSourceChange(track_name, source) {
    socket.emit('set_rec_source', {track: track_name, source: source});
}

function onMuteChange(track_name, enabled) {
    socket.emit('set_mute', {track: track_name, enabled: enabled});
}

function onSoloChange(track_name, enabled) {
    socket.emit('set_solo', {track: track_name, enabled: enabled});
}

function onPanChange(track_name, pan) {
    socket.emit('set_pan', {track: track_name, pan: pan});
}

function onVolumeDown(track_name) {
    socket.emit('volume_down', {track: track_name});
}

function onVolumeUp(track_name) {
    socket.emit('volume_up', {track: track_name});
}

function onChangeTempoBy(delta) {
    socket.emit('change_tempo_by', {delta: delta});
}

function onSetTimeSig(time_sig) {
    socket.emit('set_time_sig', {time_sig: time_sig});
}

function onTrackNameChange(old_name, new_name) {
    socket.emit('rename_track', {track: old_name, new_name: new_name});
}

function onRemoveTrack(track_name) {
    socket.emit('remove_track', {track: track_name});
}

function onMoveTrackUp(track_name) {
    socket.emit('move_track_up', {track: track_name});
}

function onMoveTrackDown(track_name) {
    socket.emit('move_track_down', {track: track_name});
}

class UpperControlPanelRow extends Component {
  render() {
    return <div className="upper-control-panel-row">
      <input className="image-button" type="image" src="/record.svg"
             id="start-recording"
             onClick={this.props.onStartRecording} />
      <input className="image-button" type="image" src="/play-pause.svg"
             onClick={this.props.onPlayStop} />
      <input className="image-button" type="image" src="/remove-arm-for-recording.svg" />
    </div>;
  }
}

class MoreOptions extends Component {
  render() {
    const status_icon =
      this.props.audioIoRunning
        ? <input className="image-button" type="image" src="/status-good.svg" />
        : <input className="image-button" type="image" src="/status-bad.svg" />;

    const session_icon =
      <input className="image-button" type="image" src="/session.svg" />;

    const timing_icon =
      <input className="image-button" type="image" src="/metronome.svg" />;

    const marks_icon =
      <input className="image-button" type="image" src="/mark.svg" />;

    const rec_icon =
      <input className="image-button" type="image" src="/microphone.svg" />;

    const transport_icon =
      <input className="image-button" type="image" src="/transport.svg" />;

    return <div id="more-options">
      <Tabs>
        <TabList>
          <Tab>{status_icon}</Tab>
          <Tab>{session_icon}</Tab>
          <Tab>{timing_icon}</Tab>
          <Tab>{marks_icon}</Tab>
          <Tab>{rec_icon}</Tab>
          <Tab>{transport_icon}</Tab>
        </TabList>

        <TabPanel>
          <Status
            pingLatency={this.props.pingLatency}
            audioIoRunning={this.props.audioIoRunning}
            onStartAudio={onStartAudio}
            onStopAudio={onStopAudio}/>
        </TabPanel>
        <TabPanel>
          <SessionManagement
            session={this.props.session}
            track_edit_mode={this.props.trackEditMode}
            onSetTrackEditMode={this.props.onSetTrackEditMode}
            workspace_sessions={this.props.workspaceSessions}
            onNewSession={onNewSession}
            onLoadSession={onLoadSession}
            onSaveSession={onSaveSession}
            onSaveSessionAs={onSaveSessionAs} />
        </TabPanel>
        <TabPanel>
          <TimingManagement
            session={this.props.session}
            onToggleMetronome={onToggleMetronome}
            onMetronomeVolDown={onMetronomeVolDown}
            onMetronomeVolUp={onMetronomeVolUp}
            onChangeTempoBy={onChangeTempoBy}
            onSetTimeSig={onSetTimeSig}
            onSessionTiming={onSessionTiming}
            onAudacityTiming={onAudacityTiming} />
        </TabPanel>
        <TabPanel>
          <Marks
            session={this.props.session}
            current_bar={this.props.currentBar}
            onSetMarkAtBar={onSetMarkAtBar} />
        </TabPanel>
        <TabPanel>
          <RecordedFragments
            recorded_fragments={this.props.recordedFragments}
            onCommit={this.props.onCommit}/>
        </TabPanel>
        <TabPanel>
          <TransportControl
            session={this.props.session}
            current_position={this.props.currentPosition}
            current_beat={this.props.currentBeat}
            current_bar={this.props.currentBar}
            autoRewind={this.props.autoRewind}
            onSetAutoRewind={onSetAutoRewind}
            onGoToBeat={this.props.onGoToBeat}
            onGoToBar={this.props.onGoToBar}/>
        </TabPanel>
      </Tabs>
    </div>;
  }
}

class LowerControlPanelRow extends Component {
  render() {
    return <div className="lower-control-panel-row">
      <input className="image-button" type="image" src="/A.svg"
             onClick={evt => this.props.onGoToMark("a")}/>
      <input className="image-button" type="image" src="/B.svg"
             onClick={evt => this.props.onGoToMark("b")}/>
      <input className="image-button" type="image" src="/rewind.svg"
             onClick={evt => this.props.onGoToBeat(0)}/>
      {
        this.props.main_view_mode === 'mixer'
          ? <input className="image-button" type="image" src="/more.svg"
              onClick={evt => this.props.onToggleMainViewMode()}/>
          : <input className="image-button highlighted-button" type="image" src="/more.svg"
              onClick={evt => this.props.onToggleMainViewMode()}/>
      }
    </div>;
  }
}

export class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      track_edit_mode: false,
      main_view_mode: 'mixer',
    };
  }
  render() {
    const { tracks=[] } = this.props.session || {};
    const track_metering_data = this.props.track_metering_data || {};

    const position_seconds = this.props.position_seconds || 0;
    const fragment_length =
      (tracks.length > 0 && track_metering_data[tracks[0].name])
      ? track_metering_data[tracks[0].name].fragment_length
      : NaN;
    const current_index = Math.floor(position_seconds / fragment_length);

    const audible = calculate_tracks_audibility(tracks, this.props.is_transport_rolling);
    const meter_values = tracks.reduce((result, track) => {
      if (!audible[track.name]) {
        result[track.name] = -200;
        return result;
      }
      const { rms=[], peak=[] } = track_metering_data[track.name] || {};
      const rms_prefader = rms[current_index] || -200;
      const peak_prefader = peak[current_index] || -200;
      result[track.name] = {rms: rms_prefader + track.vol_dB, peak: peak_prefader + track.vol_dB};
      return result;
    }, {});
    const playback_current_rms = tracks
      .map(track => gains_for_track(track, meter_values[track.name].rms))
      .reduce((result, gain) => {
        return [result[0] + gain[0], result[1] + gain[1]];
      }, [0.0, 0.0]).map(factor => factor_to_dB(factor));

    return <div className="full-area">
      <SummaryLine
          is_audio_io_running={this.props.is_audio_io_running}
          session={this.props.session}
          current_position={this.props.current_position}
          current_beat={this.props.current_beat} />
      <div className="control-panel">
        <UpperControlPanelRow
          onPlayStop={onPlayStop}
          onStartRecording={onStartRecording} />
        <LowerControlPanelRow
          ping_latency={this.props.ping_latency}
          track_edit_mode={this.state.track_edit_mode}
          onSetTrackEditMode={(value) => this.updateTrackEditMode(value)}
          session={this.props.session}
          is_audio_io_running={this.props.is_audio_io_running}
          workspace_sessions={this.props.workspace_sessions}
          recorded_fragments={this.props.recorded_fragments}
          onCommit={onCommit}
          onGoToBeat={onGoToBeat}
          onGoToMark={onGoToMark}
          current_position={this.props.current_position}
          current_beat={this.props.current_beat}
          current_bar={this.props.current_bar}
          main_view_mode={this.state.main_view_mode}
          onToggleMainViewMode={() => this.toggleMainViewMode()} />
        <PlaybackCaptureMeters
          capture_meter={this.props.capture_meter}
          playback_meter={playback_current_rms} />
      </div>
      <div className="main-view">
      {
        this.state.main_view_mode === 'mixer'
         ? <Tracks
             track_edit_mode={this.state.track_edit_mode}
             onSetTrackEditMode={value => this.updateTrackEditMode(value)}
             session={this.props.session}
             meter_values={meter_values}
             onRecChange={onRecChange}
             onRecSourceChange={onRecSourceChange}
             onMuteChange={onMuteChange}
             onSoloChange={onSoloChange}
             onPanChange={onPanChange}
             onVolumeDown={onVolumeDown}
             onVolumeUp={onVolumeUp}
             onAddTrack={onAddTrack}
             onNameChange={onTrackNameChange}
             onRemove={onRemoveTrack}
             onMoveUp={onMoveTrackUp}
             onMoveDown={onMoveTrackDown} />
         : <MoreOptions
             pingLatency={this.props.ping_latency}
             audioIoRunning={this.props.is_audio_io_running}
             trackEditMode={this.state.track_edit_mode}
             onSetTrackEditMode={value => this.updateTrackEditMode(value)}
             workspaceSessions={this.props.workspace_sessions}
             session={this.props.session}
             recordedFragments={this.props.recorded_fragments}
             onCommit={this.props.onCommit}
             currentPosition={this.props.current_position}
             currentBar={this.props.current_bar}
             autoRewind={this.props.autoRewind}
             currentBeat={this.props.current_beat}
             onGoToBeat={this.props.onGoToBeat}
             onGoToBar={this.props.onGoToBar} />
      }
      </div>
    </div>;
  }
  updateTrackEditMode(value) {
    this.setState({
      track_edit_mode: value,
      main_view_mode: value ? 'mixer' : 'options',
    });
  }
  toggleMainViewMode() {
    this.setState({
      main_view_mode: this.state.main_view_mode === 'mixer' ? 'options' : 'mixer'
    });
  }
}