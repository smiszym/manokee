import React, {Component} from "react";

export class Timing extends Component {
  render() {
    return <div>
      <h2>Timing</h2>
      <button onClick={this.props.onSessionTiming}>Session</button>
      <button onClick={this.props.onAudacityTiming}>Audacity</button>
    </div>;
  }
}
