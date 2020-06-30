import React, {Component} from "react";
import Collapsible from "react-collapsible";

export class Marks extends Component {
  render() {
    const {marks = {}} = this.props.session || {};
    return <Collapsible trigger={<button>Marks...</button>}>
      <div>
        <button>Set mark here</button>
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
    </Collapsible>;
  }
}
