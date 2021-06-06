import React, { Component } from "react";
import { AudioIoControl } from "./audio-io-control";

export class Status extends Component {
  render() {
    const track_memory_usage_mb = this.props.track_memory_usage_mb || {};

    return (
      <div>
        <div className="ui-latency-info">
          UI latency: {(this.props.pingLatency * 1000).toFixed(0)} ms
        </div>
        <div className="ui-latency-info">
          Memory:
          <br />
          used by Manokee:
          {(this.props.process_rss / 1024 / 1024).toFixed(0)} MB (
          {(this.props.process_rss / 2 / 48000 / 60).toFixed(0)} minutes of 48
          kHz mono audio)
          <br />
          available:
          {(this.props.available_ram / 1024 / 1024).toFixed(0)} MB (
          {(this.props.available_ram / 2 / 48000 / 60).toFixed(0)} minutes of 48
          kHz mono audio)
        </div>
        <div>
          <ul>
            {Object.entries(track_memory_usage_mb).map((track) => {
              const name = track[0];
              const memory_usage_mb = track[1];
              return (
                <li key={name}>
                  {name}: {memory_usage_mb} MB
                </li>
              );
            })}
            <li>
              TOTAL TRACKS:
              {Object.values(track_memory_usage_mb).reduce(
                (acc, val) => acc + val,
                0
              )}{" "}
              MB
            </li>
          </ul>
        </div>
        <AudioIoControl
          is_audio_io_running={this.props.audioIoRunning}
          onStartAudio={this.props.onStartAudio}
          onStopAudio={this.props.onStopAudio}
        />
        Manokee uses the excellent{" "}
        <a
          target="_blank"
          href="https://www.fontspace.com/cute-aurora-font-f46818"
        >
          Cute Aurora font by 611 Studio
        </a>
        .
      </div>
    );
  }
}
