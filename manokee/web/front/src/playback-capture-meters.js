import React, { Component } from "react";
import { Meter } from "./meter";

export class PlaybackCaptureMeters extends Component {
  render() {
    const capture_meter = this.props.capture_meter || [-200, -200];
    const playback_meter = this.props.playback_meter || [-200, -200];
    return (
      <div className="main-meters">
        <div>
          Capture:
          <Meter rms={capture_meter[0]} peak={-200} />
          <Meter rms={capture_meter[1]} peak={-200} />
        </div>
        <div>
          Playback:
          <Meter rms={playback_meter[0]} peak={-200} />
          <Meter rms={playback_meter[1]} peak={-200} />
        </div>
      </div>
    );
  }
}
