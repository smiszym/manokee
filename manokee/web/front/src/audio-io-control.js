import React, {Component} from "react";

export class AudioIoControl extends Component {
  render() {
    return <div>
      {this.props.is_audio_io_running
        ? <input
            className="audio-io-control-button" type="image"
            src="/audio-io-running.svg" onClick={this.props.onStopAudio} />
        : <input
            className="audio-io-control-button" type="image"
            src="/audio-io-stopped.svg" onClick={this.props.onStartAudio} />}
    </div>;
  }
}
