import React, {Component} from "react";

export class Meter extends Component {
  componentDidMount() {
    this.displayedValue = -200;
    requestAnimationFrame(timestamp => this.updateCanvas(timestamp));
  }

  componentDidUpdate() {
    if (this.props.value > this.displayedValue) {
      this.displayedValue = this.props.value;
    }
  }

  updateCanvas(timestamp) {
    const ctx = this.refs.canvas.getContext('2d');
    const width = ctx.canvas.clientWidth;
    const height = ctx.canvas.clientHeight;
    const minValue = this.props.min_value || -48;
    const yellowValue = this.props.yellow_value || -9;
    const redValue = this.props.red_value || -3;
    const maxValue = this.props.max_value || 6;
    const filledWidth =
      (this.displayedValue - minValue) * width / (maxValue - minValue);
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, "#006000");
    gradient.addColorStop(1, "#909000");
    ctx.fillStyle = gradient;
    ctx.clearRect(0, 0, width, height);
    ctx.fillRect(0, 0, filledWidth, height);
    ctx.strokeStyle = '#009000';
    ctx.beginPath();
    let dB;
    for (dB = minValue; dB < yellowValue; dB += 6) {
      const x = (dB - minValue) * width / (maxValue - minValue)
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.strokeStyle = '#909000';
    ctx.beginPath();
    for (; dB < redValue; dB += 6) {
      const x = (dB - minValue) * width / (maxValue - minValue)
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.strokeStyle = '#e00000';
    ctx.beginPath();
    for (; dB <= maxValue; dB += 6) {
      const x = (dB - minValue) * width / (maxValue - minValue)
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.closePath();
    ctx.stroke();

    let timeElapsed = (timestamp - this.lastTimestamp) / 1000.0;
    this.lastTimestamp = timestamp;
    if (timeElapsed)
      this.displayedValue -= 30 * timeElapsed;  // 30 dB/s decay
    requestAnimationFrame(timestamp => this.updateCanvas(timestamp));
  }

  render() {
    return <canvas className="meter" ref="canvas" width="100%" height="8px"/>;
  }
}
