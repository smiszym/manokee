import React, { Component } from "react";
import Popup from "reactjs-popup";
import { Line } from "rc-progress";
import PanKnob from "./pan-knob";
import { Meter } from "./meter";

class EditTrackNamePopup extends Component {
  constructor(props) {
    super(props);
    this.state = {
      track_name: "",
    };
  }

  render() {
    return (
      <Popup modal trigger={this.props.trigger}>
        <div>
          {this.props.prompt}
          <input
            type="text"
            value={this.state.track_name}
            onChange={(evt) => this.updateTrackName(evt)}
          />
          <button onClick={(evt) => this.props.onSubmit(this.state.track_name)}>
            {this.props.submit_text}
          </button>
        </div>
      </Popup>
    );
  }

  updateTrackName(evt) {
    this.setState({
      track_name: evt.target.value,
    });
  }
}

export class Track extends Component {
  render() {
    const track = this.props.track;

    if (this.props.edit_mode) {
      return (
        <div className="track-table-row">
          <button
            className="track-table-col remove-track-btn"
            onClick={() => this.props.onRemove()}
          >
            ❌
          </button>
          <button
            className="track-table-col move-track-btn"
            onClick={() => this.props.onMoveUp()}
          >
            ᐃ
          </button>
          <button
            className="track-table-col move-track-btn"
            onClick={() => this.props.onMoveDown()}
          >
            ᐁ
          </button>
          <EditTrackNamePopup
            trigger={
              <div className="track-table-col track-name">
                <div>{track.name}</div>
                <Meter
                  rms={this.props.meter_rms}
                  peak={this.props.meter_peak}
                />
              </div>
            }
            prompt="New name:"
            submit_text="OK"
            onSubmit={(new_name) => this.props.onNameChange(new_name)}
          />
        </div>
      );
    } else {
      return (
        <div className="track-table-row">
          <div className="track-table-col small-button">
            <input
              className="rec-toggle"
              type="checkbox"
              checked={track.is_rec}
              onChange={(evt) => this.props.onRecChange(evt.target.checked)}
            />
          </div>
          <div className="track-table-col small-button">
            <input
              className="rec-source"
              type="checkbox"
              checked={track.rec_source === "R"}
              onChange={(evt) =>
                this.props.onRecSourceChange(evt.target.checked ? "R" : "L")
              }
            />
          </div>
          <div className="track-table-col small-button">
            <input
              className="mute-toggle"
              type="checkbox"
              checked={track.is_mute}
              onChange={(evt) => this.props.onMuteChange(evt.target.checked)}
            />
          </div>
          <div className="track-table-col small-button">
            <input
              className="solo-toggle"
              type="checkbox"
              checked={track.is_solo}
              onChange={(evt) => this.props.onSoloChange(evt.target.checked)}
            />
          </div>
          <div className="track-table-col pan-ctrl">
            <PanKnob
              pan={track.pan}
              onPanChange={(value) => this.props.onPanChange(value)}
            />
          </div>
          <div className="track-table-col vol-ctrl">
            <Popup trigger={<span>{track.vol_dB.toFixed(0)} dB</span>} modal>
              <div id="change-volume">
                <div>{track.name}</div>
                <div>{track.vol_dB.toFixed(0)} dB</div>
                <div>
                  <button onClick={(evt) => this.props.onVolumeDown()}>
                    -
                  </button>
                  <button onClick={(evt) => this.props.onVolumeUp()}>+</button>
                </div>
              </div>
            </Popup>
          </div>
          <div className="track-table-col track-name">
            <div>
              {track.requires_audio_save ? "*" : ""}
              {track.name}
            </div>
            {track.is_loaded ? (
              <Meter rms={this.props.meter_rms} peak={this.props.meter_peak} />
            ) : (
              <Line
                style={{ width: "100%", height: "8px", display: "block" }}
                percent={track.percent_loaded}
                strokeWidth={4}
                strokeColor="#39671f"
                trailColor="#c0e8a8"
              />
            )}
          </div>
        </div>
      );
    }
  }
}

export class AddTrackButton extends Component {
  render() {
    return (
      <EditTrackNamePopup
        trigger={
          <button className="track-table-col add-track-btn">Add track</button>
        }
        prompt="New track name:"
        submit_text="OK"
        onSubmit={(track_name) => this.props.onAddTrack(track_name)}
      />
    );
  }
}
