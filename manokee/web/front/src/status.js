import React, {Component} from "react";
import {AudioIoControl} from "./audio-io-control";

export class Status extends Component {
  render() {
    return <div>
      <div className="ui-latency-info">
        UI latency: {(this.props.pingLatency * 1000).toFixed(0)} ms
      </div>
      <div className="ui-latency-info">
        Memory:<br />
        used by Manokee:
        {(this.props.process_rss / 1024 / 1024).toFixed(0)} MB
        ({(this.props.process_rss / 2 / 48000 / 60).toFixed(0)} minutes
        of 48 kHz mono audio)
        <br />
        available:
        {(this.props.available_ram / 1024 / 1024).toFixed(0)} MB
        ({(this.props.available_ram / 2 / 48000 / 60).toFixed(0)} minutes
        of 48 kHz mono audio)
      </div>
      <AudioIoControl
        is_audio_io_running={this.props.audioIoRunning}
        onStartAudio={this.props.onStartAudio}
        onStopAudio={this.props.onStopAudio} />
    </div>;
  }
}
