import React, {Component} from "react";
import Collapsible from "react-collapsible";
import Popup from "reactjs-popup";
import {Meter} from "./meter";

class WorkspaceSessions extends Component {
  render() {
    const sessions = this.props.workspace_sessions || [];

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

class ConfirmNewSessionPopup extends Component {
  render() {
    return <Popup modal trigger={this.props.trigger}>
      {close => (
        <div>
          {this.props.prompt}
          <button
            onClick={evt => { this.props.onConfirm(); close(); }} >
            {this.props.confirm_text}
          </button>
        </div>
      )}
    </Popup>
  }
}

class EditSessionNamePopup extends Component {
  constructor(props) {
    super(props);
    this.state = {
      session_name: '',
    };
  }

  render() {
    return <Popup modal trigger={this.props.trigger}>
      <div>
        {this.props.prompt}
        <input
          type="text" value={this.state.session_name}
          onChange={evt => this.updateSessionName(evt)}/>
        <button
          onClick={evt => this.props.onSubmit(this.state.session_name)}>
          {this.props.submit_text}
        </button>
      </div>
    </Popup>
  }

  updateSessionName(evt) {
    this.setState({
      session_name: evt.target.value
    });
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
    return <div>
      <ConfirmNewSessionPopup
        trigger={<button>New session</button>}
        prompt="Are you sure you want to discard any changes and start a new session?"
        confirm_text="Create new session"
        onConfirm={this.props.onNewSession} />
      {
        this.props.session.name
          ? <button
              onClick={evt => this.props.onSaveSession()}>
              Save session
            </button>
          : <EditSessionNamePopup
              trigger={<button>Save session as...</button>}
              prompt="Name:"
              submit_text="Save"
              onSubmit={name => this.props.onSaveSessionAs(name)} />
      }
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
        <h3>Workspace</h3>
        <WorkspaceSessions
          workspace_sessions={this.props.workspace_sessions}
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
    </div>;
  }

  updateSessionPath(evt) {
    this.setState({
      session_path: evt.target.value
    });
  }
}
