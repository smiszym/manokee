import React, {Component} from "react";
import Collapsible from "react-collapsible";
import {AudioIoControl} from "./AudioIoControl";

export class Status extends Component {
  render() {
    const status_icon =
      this.props.audioIoRunning
        ? <input
                  className="image-button menu-image-button" type="image" src="/status-good.svg" />
        : <input
                  className="image-button menu-image-button" type="image" src="/status-bad.svg" />;

    return <div>
      <Collapsible trigger={status_icon}>
        <div className="ui-latency-info">
          UI latency: {(this.props.pingLatency * 1000).toFixed(0)} ms
        </div>
        <AudioIoControl
          is_audio_io_running={this.props.audioIoRunning}
          onStartAudio={this.props.onStartAudio}
          onStopAudio={this.props.onStopAudio} />
      </Collapsible>
    </div>;
  }
}
