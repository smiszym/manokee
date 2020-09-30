import React, {Component} from "react";

export class Marks extends Component {
  render() {
    const {marks = {}} = this.props.session || {};
    return <div>
      <div>
        Currently at bar {this.props.current_bar + 1}
        <button onClick={evt => this.props.onSetMarkAtBar('a', this.props.current_bar)}>
          Set mark A at this bar
        </button>
        <button onClick={evt => this.props.onSetMarkAtBar('b', this.props.current_bar)}>
          Set mark B at this bar
        </button>
      </div>
      <div><b>Currently set marks:</b></div>
      <div className="mark-table">
        <div className="mark-table-row">
          <div className="mark-table-col"><b>name</b></div>
          <div className="mark-table-col"><b>position</b></div>
        </div>
        {
          Object.keys(marks).map((name, i) => {
            const position = marks[name];
            return <div key={name} className="mark-table-row">
              <div className="mark-table-col">{name}</div>
              <div className="mark-table-col">{position}</div>
            </div>;
          })
        }
      </div>
    </div>;
  }
}
