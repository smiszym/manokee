import React, { Component } from "react";
import { AddTrackButton, Track } from "./tracks";

class TrackGroup extends Component {
  render() {
    const { tracks = [] } = this.props.trackGroup || {};
    return (
      <div>
        {!this.props.isFirstGroup ? <hr /> : null}
        <div
          className={
            "track-table " +
            (this.props.isActive
              ? "active-track-group"
              : "inactive-track-group")
          }
        >
          {tracks.map((track, i) => {
            const meterValues = this.props.meter_values[track.name];

            return (
              <Track
                key={track.name}
                track={track}
                edit_mode={this.props.track_edit_mode}
                meter_rms={this.props.isActive ? meterValues.rms : -200}
                meter_peak={this.props.isActive ? meterValues.peak : -200}
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
            <AddTrackButton
              groupName={this.props.trackGroup.name}
              onAddTrack={this.props.onAddTrack}
            />
          </div>
        )}
      </div>
    );
  }
}

export class AllTrackGroups extends Component {
  render() {
    const { trackGroups = [] } = this.props.session || {};
    return (
      <div>
        {trackGroups.map((group, i) => {
          return (
            <TrackGroup
              key={group.name}
              trackGroup={group}
              isActive={this.props.activeTrackGroupName == group.name}
              isFirstGroup={i == 0}
              track_edit_mode={this.props.track_edit_mode}
              meter_values={this.props.meter_values}
              onRecChange={this.props.onRecChange}
              onRecSourceChange={this.props.onRecSourceChange}
              onMuteChange={this.props.onMuteChange}
              onSoloChange={this.props.onSoloChange}
              onPanChange={this.props.onPanChange}
              onVolumeDown={this.props.onVolumeDown}
              onVolumeUp={this.props.onVolumeUp}
              onNameChange={this.props.onNameChange}
              onRemove={this.props.onRemove}
              onMoveDown={this.props.onMoveDown}
              onMoveUp={this.props.onMoveUp}
              onAddTrack={this.props.onAddTrack}
            />
          );
        })}
      </div>
    );
  }
}
