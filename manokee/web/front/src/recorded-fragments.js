import React, { Component } from "react";

class Fragment extends Component {
  render() {
    return (
      <div className="fragment-table-row">
        <div className="fragment-table-col">
          {this.props.transport_state}
          <button onClick={(evt) => this.props.onCommit()}>commit</button>
        </div>
        <div className="fragment-table-col">{this.props.starting_time}</div>
        <div className="fragment-table-col">{this.props.length}</div>
      </div>
    );
  }
}

export class RecordedFragments extends Component {
  render() {
    const recorded_fragments = this.props.recorded_fragments || [];

    return (
      <div>
        <div className="fragment-table">
          <div className="fragment-table-row">
            <div className="fragment-table-col">
              <b>state</b>
            </div>
            <div className="fragment-table-col">
              <b>start</b>
            </div>
            <div className="fragment-table-col">
              <b>length</b>
            </div>
          </div>
          {recorded_fragments.map((fragment, i) => {
            return (
              <Fragment
                key={fragment.id}
                transport_state={fragment.transport_state}
                starting_time={fragment.starting_time}
                length={fragment.length}
                onCommit={() => this.props.onCommit(fragment.id)}
              />
            );
          })}
        </div>
      </div>
    );
  }
}
