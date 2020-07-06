import React, {Component} from "react";
import Collapsible from "react-collapsible";

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

export class SessionManagement extends Component {
  constructor(props) {
    super(props);
    this.state = {
      session_path: '',
    };
  }

  render() {
    return <div>
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
      <button>Render session</button>
      <button>Export to Ardour</button>
      <button>Export to zip-packed wav</button>
      <div>
        <button>Import music file:</button>
        <input id="music-file-path" type="text"/>
      </div>
    </div>;
  }

  updateSessionPath(evt) {
    this.setState({
      session_path: evt.target.value
    });
  }
}
