import React, {Component} from "react";
import {Meter} from "./Meter";

export class PlaybackCaptureMeters extends Component {
  render() {
    const capture_meter = this.props.capture_meter || [-200, -200];
    const playback_meter = this.props.playback_meter || [-200, -200];
    return <div className="main-meters">
      <div>
        Capture:
        <Meter value={capture_meter[0]}/>
        <Meter value={capture_meter[1]}/>
      </div>
      <div>
        Playback:
        <Meter value={playback_meter[0]}/>
        <Meter value={playback_meter[1]}/>
      </div>
    </div>;
  }
}
