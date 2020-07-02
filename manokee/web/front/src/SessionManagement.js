import React, {Component} from "react";
import Collapsible from "react-collapsible";

class RecentSessions extends Component {
  render() {
    const sessions = this.props.recent_sessions || [];

    return <div>
      {
        sessions.map((session, i) => {
          return <div key={session}>
            <button
              onClick={evt => this.props.onLoadSession(session)}>
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
    const {configuration = {}} = this.props.session || {};
    const {
      bpm = '',
      time_sig = '',
      intro_len = '',
      met_intro_only = '',
      metronome = '',
      metronome_vol = '',
      metronome_pan = '',
    } = configuration || {};

    return <div>
      <Collapsible trigger={<input
                              className="image-button menu-image-button"
                              type="image"
                              src="/session.svg" />}>
        <button
          onClick={evt => this.props.onSaveSession()}>
          Save session
        </button>
        <Collapsible trigger={<button>Load session...</button>}>
          <h3>Load session from file</h3>
          Path:
          <input
            id="session-path" type="text" value={this.state.session_path}
            onChange={evt => this.updateSessionPath(evt)}/>
          <button
            onClick={evt => this.props.onLoadSession(this.state.session_path)}>
            Load
          </button>
          <h3>Recent sessions</h3>
          <RecentSessions
            recent_sessions={this.props.recent_sessions}
            onLoadSession={this.props.onLoadSession}/>
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
        <button>Render session</button>
        <button>Export to Ardour</button>
        <button>Export to zip-packed wav</button>
        <div>
          <button>Import music file:</button>
          <input id="music-file-path" type="text"/>
        </div>
      </Collapsible>
      <Collapsible trigger={<input
        className="image-button menu-image-button" type="image" src="/metronome.svg"/>}>
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
          <button onClick={this.props.onSessionTiming}>Session timing</button>
          <button onClick={this.props.onAudacityTiming}>Audacity timing</button>
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
