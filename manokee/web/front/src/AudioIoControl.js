import React, {Component} from "react";

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
