import React, {Component} from "react";

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
        <div>Tempo: {bpm} bpm</div>
        <div>Time signature: {time_sig}/4</div>
        <div>Intro length: {intro_len} beats</div>
        <div>Metronome only audible on intro: {met_intro_only}</div>
        <div>Metronome enabled: {metronome}</div>
        <div>Metronome volume: {metronome_vol}</div>
        <div>Metronome pan: {metronome_pan}</div>
        <button onClick={this.props.onSessionTiming}>Session timing</button>
        <button onClick={this.props.onAudacityTiming}>Audacity timing</button>
      </div>
    </div>;
  }
}
