import React, { Component } from "react";

export class Meter extends Component {
  componentDidMount() {
    this.displayedRms = -200;
    this.displayedPeak = -200;
    this.callback = requestAnimationFrame((timestamp) =>
      this.updateCanvas(timestamp)
    );
  }

  componentWillUnmount() {
    if (this.callback) {
      cancelAnimationFrame(this.callback);
      this.callback = null;
    }
  }

  componentDidUpdate() {
    if (this.props.rms > this.displayedRms) {
      this.displayedRms = this.props.rms;
    }
    if (this.props.peak > this.displayedPeak) {
      this.displayedPeak = this.props.peak;
      this.peakBumpedAt = this.lastTimestamp;
    }
  }

  updateCanvas(timestamp) {
    const ctx = this.refs.canvas.getContext("2d");
    const width = ctx.canvas.clientWidth;
    const height = ctx.canvas.clientHeight;
    const minValue = this.props.min_value || -48;
    const yellowValue = this.props.yellow_value || -9;
    const redValue = this.props.red_value || -3;
    const maxValue = this.props.max_value || 6;
    const fraction = (value) => (value - minValue) / (maxValue - minValue);
    const filledWidth = fraction(this.displayedRms) * width;
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0.0, "#00e000");
    gradient.addColorStop(fraction(yellowValue), "#c0f000");
    gradient.addColorStop(fraction(redValue), "#ffff00");
    gradient.addColorStop(1.0, "#ff0000");
    ctx.fillStyle = gradient;
    ctx.clearRect(0, 0, width, height);
    ctx.fillRect(0, 0, filledWidth, height);
    ctx.strokeStyle = "#006000";
    ctx.beginPath();
    let dB;
    for (dB = minValue; dB < yellowValue; dB += 6) {
      const x = ((dB - minValue) * width) / (maxValue - minValue);
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.strokeStyle = "#707000";
    ctx.beginPath();
    for (; dB < redValue; dB += 6) {
      const x = ((dB - minValue) * width) / (maxValue - minValue);
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.strokeStyle = "#b00000";
    ctx.beginPath();
    for (; dB <= maxValue; dB += 6) {
      const x = ((dB - minValue) * width) / (maxValue - minValue);
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();
    if (this.displayedPeak < yellowValue) ctx.strokeStyle = "#00e000";
    else if (this.displayedPeak < redValue) ctx.strokeStyle = "#ffff00";
    else ctx.strokeStyle = "#ff0000";
    ctx.beginPath();
    const peakX =
      ((this.displayedPeak - minValue) * width) / (maxValue - minValue);
    ctx.moveTo(peakX, 0);
    ctx.lineTo(peakX, height);
    ctx.closePath();
    ctx.stroke();

    let timeElapsed = (timestamp - this.lastTimestamp) / 1000.0;
    this.lastTimestamp = timestamp;
    if (timeElapsed) this.displayedRms -= 30 * timeElapsed; // 30 dB/s decay
    if (timestamp - this.peakBumpedAt > 1000.0) {
      this.displayedPeak = this.props.peak;
      this.peakBumpedAt = timestamp;
    }
    this.callback = requestAnimationFrame((timestamp) =>
      this.updateCanvas(timestamp)
    );
  }

  render() {
    return <canvas className="meter" ref="canvas" width="100%" height="8px" />;
  }
}
