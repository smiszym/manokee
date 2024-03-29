import React, { Component } from "react";

export class SummaryLine extends Component {
  render() {
    const { name = "", are_controls_modified = false } =
      this.props.session || {};

    return (
      <div className="summary-line">
        {this.props.is_audio_io_running ? (
          <div className="audio-ok">
            OK / {are_controls_modified ? "*" : ""}
            {name || "(untitled)"}
          </div>
        ) : (
          <div className="no-audio">NO AUDIO</div>
        )}
        <div>
          {this.props.current_position} ({this.props.current_beat})
        </div>
        <div>
          {this.props.fragment_being_revised_id !== null &&
            "revising " + this.props.fragment_being_revised_id}
        </div>
      </div>
    );
  }
}
