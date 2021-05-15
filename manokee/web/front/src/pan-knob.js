import React, { Component } from "react";
import { Knob } from "react-rotary-knob";

export default class PanKnob extends Component {
  render() {
    return (
      <Knob
        clampMin={30}
        clampMax={330}
        rotateDegrees={180}
        defaultValue={this.props.pan}
        min={-1.0}
        max={1.0}
        step={0.1}
        unlockDistance={30}
        onChange={(value) => this.props.onPanChange(value)}
      />
    );
  }
}
