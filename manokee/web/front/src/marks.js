import React, { Component } from "react";

export class Marks extends Component {
  render() {
    const { marks = {} } = this.props.session || {};
    return (
      <div>
        <div>
          Currently at bar {this.props.current_bar + 1}
          <button
            onClick={(evt) =>
              this.props.onSetMarkAtBar("a", this.props.current_bar)
            }
          >
            Set mark A at this bar
          </button>
          <button
            onClick={(evt) =>
              this.props.onSetMarkAtBar("b", this.props.current_bar)
            }
          >
            Set mark B at this bar
          </button>
        </div>
        <div>
          <b>Currently set marks:</b>
        </div>
        <div>
          {Object.entries(marks)
            .sort((a, b) => a[1].localeCompare(b[1]))
            .map((mark) => {
              const name = mark[0];
              const position = mark[1];
              return (
                <div key={name}>
                  <button onClick={(evt) => this.props.onGoToMark(name)}>
                    {name} ({position})
                  </button>
                </div>
              );
            })}
        </div>
      </div>
    );
  }
}
