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

class Track extends Component {
  render() {
    const track = this.props.track;

    return (
      <div className="track-table-row">
        {!this.props.edit_mode && (
          <div className="track-table-col small-button">
            <input
              className="rec-toggle"
              type="checkbox"
              checked={track.is_rec}
              onChange={(evt) => this.props.onRecChange(evt.target.checked)}
            />
          </div>
        )}
        {!this.props.edit_mode && (
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
        )}
        {!this.props.edit_mode && (
          <div className="track-table-col small-button">
            <input
              className="mute-toggle"
              type="checkbox"
              checked={track.is_mute}
              onChange={(evt) => this.props.onMuteChange(evt.target.checked)}
            />
          </div>
        )}
        {!this.props.edit_mode && (
          <div className="track-table-col small-button">
            <input
              className="solo-toggle"
              type="checkbox"
              checked={track.is_solo}
              onChange={(evt) => this.props.onSoloChange(evt.target.checked)}
            />
          </div>
        )}
        {!this.props.edit_mode && (
          <div className="track-table-col pan-ctrl">
            <PanKnob
              pan={track.pan}
              onPanChange={(value) => this.props.onPanChange(value)}
            />
          </div>
        )}
        {!this.props.edit_mode && (
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
        )}
        {this.props.edit_mode && (
          <button
            className="track-table-col remove-track-btn"
            onClick={(evt) => this.props.onRemove()}
          >
            ❌
          </button>
        )}
        {this.props.edit_mode && (
          <button
            className="track-table-col move-track-btn"
            onClick={(evt) => this.props.onMoveUp()}
          >
            ᐃ
          </button>
        )}
        {this.props.edit_mode && (
          <button
            className="track-table-col move-track-btn"
            onClick={(evt) => this.props.onMoveDown()}
          >
            ᐁ
          </button>
        )}
        {this.props.edit_mode ? (
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
        ) : (
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
        )}
      </div>
    );
  }
}

class AddTrackButton extends Component {
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

export class Tracks extends Component {
  render() {
    const { tracks = [] } = this.props.session || {};
    return (
      <div>
        <div className="track-table">
          {tracks.map((track, i) => {
            return (
              <Track
                key={track.name}
                track={track}
                edit_mode={this.props.track_edit_mode}
                meter_rms={this.props.meter_values[track.name].rms}
                meter_peak={this.props.meter_values[track.name].peak}
                onRecChange={(is_enabled) =>
                  this.props.onRecChange(track.name, is_enabled)
                }
                onRecSourceChange={(source) =>
                  this.props.onRecSourceChange(track.name, source)
                }
                onMuteChange={(is_enabled) =>
                  this.props.onMuteChange(track.name, is_enabled)
                }
                onSoloChange={(is_enabled) =>
                  this.props.onSoloChange(track.name, is_enabled)
                }
                onPanChange={(pan) => this.props.onPanChange(track.name, pan)}
                onVolumeDown={() => this.props.onVolumeDown(track.name)}
                onVolumeUp={() => this.props.onVolumeUp(track.name)}
                onNameChange={(new_name) =>
                  this.props.onNameChange(track.name, new_name)
                }
                onRemove={() => this.props.onRemove(track.name)}
                onMoveDown={() => this.props.onMoveDown(track.name)}
                onMoveUp={() => this.props.onMoveUp(track.name)}
              />
            );
          })}
        </div>
        {this.props.track_edit_mode && (
          <div>
            <AddTrackButton onAddTrack={this.props.onAddTrack} />
          </div>
        )}
      </div>
    );
  }
}
