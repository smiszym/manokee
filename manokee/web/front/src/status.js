import React, {Component} from "react";
import {AudioIoControl} from "./audio-io-control";

export class Status extends Component {
  render() {
    return <div>
      <div className="ui-latency-info">
        UI latency: {(this.props.pingLatency * 1000).toFixed(0)} ms
      </div>
      <AudioIoControl
        is_audio_io_running={this.props.audioIoRunning}
        onStartAudio={this.props.onStartAudio}
        onStopAudio={this.props.onStopAudio} />
    </div>;
  }
}
