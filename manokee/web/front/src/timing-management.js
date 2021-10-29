import React, { Component } from "react";
import Popup from "reactjs-popup";

import PanKnob from "./pan-knob";

class TimeSignatureChangeButton extends Component {
  render() {
    return (
      <Popup modal trigger={<button>Change time signature...</button>}>
        <div>
          Time signature:
          <button onClick={() => this.props.onSetTimeSig(1)}>1/4</button>
          <button onClick={() => this.props.onSetTimeSig(2)}>2/4</button>
          <button onClick={() => this.props.onSetTimeSig(3)}>3/4</button>
          <button onClick={() => this.props.onSetTimeSig(4)}>4/4</button>
          <button onClick={() => this.props.onSetTimeSig(5)}>5/4</button>
          <button onClick={() => this.props.onSetTimeSig(6)}>6/4</button>
          <button onClick={() => this.props.onSetTimeSig(7)}>7/4</button>
          <button onClick={() => this.props.onSetTimeSig(8)}>8/4</button>
          <button onClick={() => this.props.onSetTimeSig(9)}>9/4</button>
        </div>
      </Popup>
    );
  }
}

class TempoChangeButton extends Component {
  render() {
    return (
      <Popup modal trigger={<button>Change tempo...</button>}>
        <div>
          <button
            onClick={() => this.props.onChangeTempoBy(this.props.groupName, -5)}
          >
            -5
          </button>
          <button
            onClick={() => this.props.onChangeTempoBy(this.props.groupName, -1)}
          >
            -1
          </button>
          <button
            onClick={() => this.props.onChangeTempoBy(this.props.groupName, +1)}
          >
            +1
          </button>
          <button
            onClick={() => this.props.onChangeTempoBy(this.props.groupName, +5)}
          >
            +5
          </button>
        </div>
      </Popup>
    );
  }
}

export class TimingManagement extends Component {
  render() {
    const { configuration = {} } = this.props.session || {};
    const {
      time_sig = "",
      metronome = "",
      metronome_vol = "",
      metronome_pan = "",
    } = configuration || {};

    function renderTrackGroup(
      group,
      activeTrackGroupName,
      onChangeTempoBy,
      onSetActiveTrackGroup
    ) {
      const timing = group.timing;
      const bpmInfo =
        timing.type === "fixed-bpm"
          ? [
              timing.bpm.toFixed(0),
              "bpm",
              <TempoChangeButton
                onChangeTempoBy={onChangeTempoBy}
                groupName={group.name}
              />,
            ]
          : timing.type === "audacity"
          ? [timing.averageBpm.toFixed(0), "bpm on average"]
          : undefined;

      return (
        <li key={group.name}>
          <button
            key={group.name}
            className={
              activeTrackGroupName == group.name ? "highlighted-button" : ""
            }
            onClick={() => onSetActiveTrackGroup(group.name)}
          >
            {group.name ? group.name : "Main group"}
          </button>
          {bpmInfo}
        </li>
      );
    }

    return (
      <div>
        <div>
          <button onClick={() => this.props.onToggleMetronome()}>Toggle</button>
          <button onClick={() => this.props.onMetronomeVolDown()}>-</button>
          <button onClick={() => this.props.onMetronomeVolUp()}>+</button>
          <div>Time signature: {time_sig}/4</div>
          <TimeSignatureChangeButton onSetTimeSig={this.props.onSetTimeSig} />
          <div>Metronome {metronome == "1" ? "on" : "off"}</div>
          <div>Metronome volume: {parseFloat(metronome_vol).toFixed(1)} dB</div>
          <div>
            Metronome pan:
            <PanKnob
              pan={metronome_pan}
              onPanChange={(value) => this.props.onMetronomePanChange(value)}
            />
          </div>
          <div>
            <ul>
              {this.props.session.trackGroups.map((group) =>
                renderTrackGroup(
                  group,
                  this.props.active_track_group_name,
                  this.props.onChangeTempoBy,
                  this.props.onSetActiveTrackGroup
                )
              )}
            </ul>
          </div>
          <div>Playback is {this.props.is_looped ? "" : "not"} looped.</div>
          {this.props.session.trackGroups.length >= 2 && (
            <div>
              <button
                onClick={(evt) =>
                  this.props.onSetLoopSpec([
                    { bar_a: "a", bar_b: "b", track_group_name: "" },
                    {
                      bar_a: "a",
                      bar_b: "b",
                      track_group_name: this.props.session.trackGroups[1].name,
                    },
                  ])
                }
              >
                Loop A-B main / {this.props.session.trackGroups[1].name}
              </button>
              <button
                onClick={(evt) =>
                  this.props.onSetLoopSpec([
                    { bar_a: "a", bar_b: "b", track_group_name: "" },
                  ])
                }
              >
                Loop A-B main
              </button>
              <button
                onClick={(evt) =>
                  this.props.onSetLoopSpec([
                    {
                      bar_a: "a",
                      bar_b: "b",
                      track_group_name: this.props.session.trackGroups[1].name,
                    },
                  ])
                }
              >
                Loop A-B {this.props.session.trackGroups[1].name}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }
}
