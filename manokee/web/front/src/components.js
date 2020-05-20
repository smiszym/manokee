import React, { Component } from 'react';
import Collapsible from 'react-collapsible';
import Popup from 'reactjs-popup';

export class SummaryLine extends Component {
  render() {
    const { name="", are_controls_modified=false } = this.props.session || {};

    return <div className="summary-line">
      <div className="summary-entries">
        {this.props.is_audio_io_running
          ? <div className="audio-ok">
              OK / {are_controls_modified?"*":""}{name}
            </div>
          : <div className="no-audio">NO AUDIO</div>}
        <div>{this.props.current_position} ({this.props.current_beat})</div>
        <div>recording info</div>
      </div>
    </div>;
  }
}

export class AudioIoControl extends Component {
  render() {
    return <div>
      {this.props.is_audio_io_running
        ? <span className="audio-ok">Audio IO is running</span>
        : <span className="no-audio">Audio IO is not running</span>}
      {this.props.is_audio_io_running
        ? <button onClick={this.props.onStopAudio}>Stop audio I/O</button>
        : <button onClick={this.props.onStartAudio}>Start audio I/O</button>}
    </div>;
  }
}

class Meter extends Component {
  componentDidMount() {
    this.updateCanvas();
  }
  componentDidUpdate() {
    this.updateCanvas();
  }
  updateCanvas() {
    const ctx = this.refs.canvas.getContext('2d');
    const width = ctx.canvas.clientWidth;
    const height = ctx.canvas.clientHeight;
    const minValue = this.props.min_value || -48;
    const maxValue = this.props.max_value || 6;
    const filledWidth =
      (this.props.value - minValue) * width / (maxValue - minValue);
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, "#006000");
    gradient.addColorStop(1, "#909000");
    ctx.fillStyle = gradient;
    ctx.clearRect(0,0, width, height);
    ctx.fillRect(0, 0, filledWidth, height);
  }
  render() {
    return <canvas className="meter" ref="canvas" width="100%" height="8px" />;
  }
}

class EditTrackNamePopup extends Component {
  constructor(props) {
    super(props);
    this.state = {
      track_name: '',
    };
  }
  render() {
    return <Popup modal
        trigger={this.props.trigger}>
      <div>
        {this.props.prompt}
        <input
          type="text" value={this.state.track_name}
          onChange={evt => this.updateTrackName(evt)} />
        <button
            onClick={evt => this.props.onSubmit(this.state.track_name)}>
          {this.props.submit_text}
        </button>
      </div>
    </Popup>
  }
  updateTrackName(evt) {
    this.setState({
      track_name: evt.target.value
    });
  }
}

class Track extends Component {
  render() {
    const track = this.props.track;

    return <div className="track-table-row">
            {!this.props.edit_mode &&
              <div className="track-table-col small-button">
                <input className="rec-toggle" type="checkbox"
                       checked={track.is_rec}
                       onChange={evt => this.props.onRecChange(
                         evt.target.checked)} />
              </div>
            }
            {!this.props.edit_mode &&
              <div className="track-table-col small-button">
                <input className="rec-source" type="checkbox"
                       checked={track.rec_source === 'R'}
                       onChange={evt => this.props.onRecSourceChange(
                         evt.target.checked ? 'R' : 'L')} />
              </div>
            }
            {!this.props.edit_mode &&
              <div className="track-table-col small-button">
                <input className="mute-toggle" type="checkbox"
                       checked={track.is_mute}
                       onChange={evt => this.props.onMuteChange(
                         evt.target.checked)} />
              </div>
            }
            {!this.props.edit_mode &&
              <div className="track-table-col small-button">
                <input className="solo-toggle" type="checkbox"
                       checked={track.is_solo}
                       onChange={evt => this.props.onSoloChange(
                         evt.target.checked)} />
              </div>
            }
            {!this.props.edit_mode &&
              <div className="track-table-col pan-ctrl">
                <input type="range" min="-1.0" max="1.0" step="0.05"
                       value={track.pan}
                       className="slider"
                       onChange={evt => this.props.onPanChange(
                         parseFloat(evt.target.value))} />
              </div>
            }
            {!this.props.edit_mode &&
              <div className="track-table-col vol-ctrl">
                <Popup trigger={<span>{track.vol_dB.toFixed(0)} dB</span>} modal>
                  <div id="change-volume">
                    <div>
                      {track.name}
                    </div>
                    <div>
                      {track.vol_dB.toFixed(0)} dB
                    </div>
                    <div>
                      <button onClick={evt => this.props.onVolumeDown()}>
                        -
                      </button>
                      <button onClick={evt => this.props.onVolumeUp()}>
                        +
                      </button>
                    </div>
                  </div>
                </Popup>
              </div>
            }
            {this.props.edit_mode &&
              <button className="track-table-col remove-track-btn"
                      onClick={evt => this.props.onRemove()} >
                ❌
              </button>
            }
            {this.props.edit_mode &&
              <button className="track-table-col move-track-btn"
                      onClick={evt => this.props.onMoveUp()} >
                ᐃ
              </button>
            }
            {this.props.edit_mode &&
              <button className="track-table-col move-track-btn"
                      onClick={evt => this.props.onMoveDown()} >
                ᐁ
              </button>
            }
            {this.props.edit_mode
              ? <EditTrackNamePopup
                  trigger={
                    <div className="track-table-col track-name">
                      <div>{track.name}</div>
                      <Meter value={current_meter_value} />
                    </div>}
                  prompt="New name:"
                  submit_text="OK"
                  onSubmit={new_name => this.props.onNameChange(new_name)} />
              : <div className="track-table-col track-name">
                  <div>{track.requires_audio_save ? "*" : ""}{track.name}</div>
                  <Meter value={this.props.meter_value} />
                </div>
            }
          </div>;
  }
}

class AddTrackButton extends Component {
  render() {
    return <EditTrackNamePopup
        trigger={<button className="track-table-col add-track-btn">
                   Add track
                 </button>}
        prompt="New track name:"
        submit_text="OK"
        onSubmit={track_name => this.props.onAddTrack(track_name)} />;
  }
}

export class Tracks extends Component {
  render() {
    const { tracks=[] } = this.props.session || {};
    return <div>
      <div className="track-table">
        {
          tracks.map((track, i) => {
            return <Track
              key={track.name} track={track}
              edit_mode={this.props.track_edit_mode}
              meter_value={this.props.meter_values[track.name]}
              onRecChange={is_enabled => this.props.onRecChange(
                track.name, is_enabled)}
              onRecSourceChange={source => this.props.onRecSourceChange(
                track.name, source)}
              onMuteChange={is_enabled => this.props.onMuteChange(
                track.name, is_enabled)}
              onSoloChange={is_enabled => this.props.onSoloChange(
                track.name, is_enabled)}
              onPanChange={pan => this.props.onPanChange(
                track.name, pan)}
              onVolumeDown={() => this.props.onVolumeDown(track.name)}
              onVolumeUp={() => this.props.onVolumeUp(track.name)}
              onNameChange={
                new_name => this.props.onNameChange(track.name, new_name)}
              onRemove={() => this.props.onRemove(track.name)}
              onMoveDown={() => this.props.onMoveDown(track.name)}
              onMoveUp={() => this.props.onMoveUp(track.name)} />
          })
        }
      </div>
      {this.props.track_edit_mode &&
        <AddTrackButton onAddTrack={this.props.onAddTrack} />
      }
    </div>;
  }
}

class RecentSessions extends Component {
  render() {
    const sessions = this.props.recent_sessions || [];

    return <div>
      {
        sessions.map((session, i) => {
          return <div key={session}>
            <button
              onClick={evt => this.props.onLoadSession(session)} >
              {session}
            </button>
          </div>
        })
      }
    </div>;
  }
}

export class SessionManagement extends Component {
  constructor(props) {
    super(props);
    this.state = {
      session_path: '',
    };
  }
  render() {
    const { configuration={} } = this.props.session || {};
    const {
      bpm='',
      time_sig='',
      intro_len='',
      met_intro_only='',
      metronome='',
      metronome_vol='',
      metronome_pan='',
    } = configuration || {};

    return <div>
      <button
        onClick={evt => this.props.onSaveSession()} >
        Save session
      </button>
      <Collapsible trigger={<button>Load session...</button>}>
        <h3>Load session from file</h3>
        Path:
        <input
          id="session-path" type="text" value={this.state.session_path}
          onChange={evt => this.updateSessionPath(evt)} />
        <button
          onClick={evt => this.props.onLoadSession(this.state.session_path)} >
          Load
        </button>
        <h3>Recent sessions</h3>
        <RecentSessions
          recent_sessions={this.props.recent_sessions}
          onLoadSession={this.props.onLoadSession} />
      </Collapsible>
      <Collapsible trigger={<button>Session options...</button>}>
        <button>Render session</button>
        <button>Export to Ardour</button>
        <button>Export to zip-packed wav</button>
        <div>
          <button>Import music file:</button>
          <input id="music-file-path" type="text"/>
        </div>
      </Collapsible>
      <div>
        {
          this.props.track_edit_mode
            ? <button onClick={evt => this.props.onSetTrackEditMode(false)}>
                Leave track edit mode
              </button>
            : <button onClick={evt => this.props.onSetTrackEditMode(true)}>
                Enter track edit mode
              </button>
        }
      </div>
      <Collapsible trigger={<button>Metronome...</button>}>
        <div>
          <button onClick={evt => this.props.onToggleMetronome()}>
            Toggle
          </button>
          <button onClick={evt => this.props.onMetronomeVolDown()}>
            -
          </button>
          <button onClick={evt => this.props.onMetronomeVolUp()}>
            +
          </button>
          <div>Tempo: {bpm} bpm</div>
          <div>Time signature: {time_sig}/4</div>
          <div>Intro length: {intro_len} beats</div>
          <div>Metronome only audible on intro: {met_intro_only}</div>
          <div>Metronome enabled: {metronome}</div>
          <div>Metronome volume: {metronome_vol}</div>
          <div>Metronome pan: {metronome_pan}</div>
        </div>
      </Collapsible>
    </div>;
  }
  updateSessionPath(evt) {
    this.setState({
      session_path: evt.target.value
    });
  }
}

export class Marks extends Component {
  render() {
    const { marks={} } = this.props.session || {};
    return <Collapsible trigger={<button>Marks...</button>}>
      <div><button>Set mark here</button></div>
      <div><b>Currently set marks:</b></div>
      <div className="mark-table">
        <div className="mark-table-row">
          <div className="mark-table-col"><b>name</b></div>
          <div className="mark-table-col"><b>position</b></div>
        </div>
      {
        Object.keys(marks).map((name, i) => {
          const position = marks[name];
          return <div key={name} className="mark-table-row">
            <div className="mark-table-col">{name}</div>
            <div className="mark-table-col">{position}</div>
          </div>;
        })
      }
      </div>
    </Collapsible>;
  }
}

export class TransportControl extends Component {
  constructor(props) {
    super(props);
    this.state = {
      beat_number: 0,
    };
  }
  render() {
    return <div>
      <div>
        Transport state: <span>unknown</span>.
      </div>
      <div>
        Current position: {this.props.current_position}
        ({this.props.current_beat}).
      </div>
      <div>
        <button>Toggle auto-rewind</button>
      </div>
      <Collapsible trigger={<button>Go to beat...</button>}>
        <input
          id="beat-number" type="number" value={this.state.beat_number + 1}
          onChange={evt => this.updateBeatNumber(evt)} />
        <button
          onClick={evt => this.props.onGoToBeat(this.state.beat_number)} >
          Go
        </button>
      </Collapsible>
      <div>
        <button>Go to beginning</button>
        <button>Previous bar</button>
        <button>Next bar</button>
      </div>
    </div>;
  }
  updateBeatNumber(evt) {
    this.setState({
      beat_number: parseInt(evt.target.value) - 1,
    });
  }
}

export class Timing extends Component {
  render() {
    return <div>
      <h2>Timing</h2>
      <button onClick={this.props.onSessionTiming}>Session</button>
      <button onClick={this.props.onAudacityTiming}>Audacity</button>
    </div>;
  }
}

class Fragment extends Component {
  render() {
    return <div className="fragment-table-row">
      <div className="fragment-table-col">
        {this.props.transport_state}
        <button onClick={evt => this.props.onCommit()}>
          commit
        </button>
      </div>
      <div className="fragment-table-col">
        {this.props.starting_time}
      </div>
      <div className="fragment-table-col">
        {this.props.length}
      </div>
    </div>;
  }
}

export class RecordedFragments extends Component {
  render() {
    const recorded_fragments = this.props.recorded_fragments || [];

    return <div>
      <Collapsible trigger={<button>Recorded fragments...</button>}>
        <div className="fragment-table">
          <div className="fragment-table-row">
            <div className="fragment-table-col">
              <b>state</b>
            </div>
            <div className="fragment-table-col">
              <b>start</b>
            </div>
            <div className="fragment-table-col">
              <b>length</b>
            </div>
          </div>
      {
        recorded_fragments.map((fragment, i) => {
          return <Fragment
                    key={fragment.id}
                    transport_state={fragment.transport_state}
                    starting_time={fragment.starting_time}
                    length={fragment.length}
                    onCommit={() => this.props.onCommit(fragment.id)} />
        })

      }
        </div>
      </Collapsible>
    </div>;
  }
}
