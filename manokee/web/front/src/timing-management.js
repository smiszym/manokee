import React, {Component} from "react";
import Popup from "reactjs-popup";

export class TimingManagement extends Component {
  render() {
    const {configuration = {}} = this.props.session || {};
    const {
      bpm = '',
      time_sig = '',
      intro_len = '',
      met_intro_only = '',
      metronome = '',
      metronome_vol = '',
      metronome_pan = '',
    } = configuration || {};

    return <div>
      <div>
        <button onClick={evt => this.props.onToggleMetronome()}>
          Toggle
        </button>
        <button onClick={evt => this.props.onMetronomeVolDown()}>
          -
        </button>
        <button onClick={evt => this.props.onMetronomeVolUp()}>
          +
        </button>
        <Popup modal trigger={<button>Change tempo...</button>}>
          <div>
            <button onClick={evt => this.props.onChangeTempoBy(-5)}>-5</button>
            <button onClick={evt => this.props.onChangeTempoBy(-1)}>-1</button>
            <button onClick={evt => this.props.onChangeTempoBy(+1)}>+1</button>
            <button onClick={evt => this.props.onChangeTempoBy(+5)}>+5</button>
            Time signature:
            <button onClick={evt => this.props.onSetTimeSig(1)}>1/4</button>
            <button onClick={evt => this.props.onSetTimeSig(2)}>2/4</button>
            <button onClick={evt => this.props.onSetTimeSig(3)}>3/4</button>
            <button onClick={evt => this.props.onSetTimeSig(4)}>4/4</button>
            <button onClick={evt => this.props.onSetTimeSig(5)}>5/4</button>
            <button onClick={evt => this.props.onSetTimeSig(6)}>6/4</button>
            <button onClick={evt => this.props.onSetTimeSig(7)}>7/4</button>
            <button onClick={evt => this.props.onSetTimeSig(8)}>8/4</button>
            <button onClick={evt => this.props.onSetTimeSig(9)}>9/4</button>
          </div>
        </Popup>
        <div>Tempo: {bpm} bpm</div>
        <div>Time signature: {time_sig}/4</div>
        <div>Metronome {metronome ? "on" : "off"}</div>
        <div>Metronome volume: {metronome_vol}</div>
        <div>Metronome pan: {metronome_pan}</div>
        <div>
          {
            this.props.session.track_group_names.map((group_name, i) => {
              return <button key={group_name} onClick={evt =>
                  this.props.onSetActiveTrackGroup(group_name)}>
                {group_name ? group_name : "Main group"}
              </button>
            })
          }
        </div>
      </div>
    </div>;
  }
}
