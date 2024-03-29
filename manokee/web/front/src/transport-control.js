import React, { Component } from "react";
import Collapsible from "react-collapsible";

export class TransportControl extends Component {
  constructor(props) {
    super(props);
    this.state = {
      beat_number: 0,
    };
  }

  render() {
    return (
      <div>
        <div>
          Transport state: <span>unknown</span>.
        </div>
        <div>
          {this.props.autoRewind ? (
            <input
              className="image-button menu-image-button highlighted-button"
              type="image"
              src="/auto-rewind.svg"
              onClick={(evt) => this.props.onSetAutoRewind(false)}
            />
          ) : (
            <input
              className="image-button menu-image-button"
              type="image"
              src="/auto-rewind.svg"
              onClick={(evt) => this.props.onSetAutoRewind(true)}
            />
          )}
        </div>
        <Collapsible trigger={<button>Go to beat...</button>}>
          <input
            id="beat-number"
            type="number"
            value={this.state.beat_number + 1}
            onChange={(evt) => this.updateBeatNumber(evt)}
          />
          <button
            onClick={(evt) => this.props.onGoToBeat(this.state.beat_number)}
          >
            Go
          </button>
        </Collapsible>
        <div>
          Go to bar:
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar - 1)}
          >
            {this.props.current_bar + 0}
          </button>
          <button
            className="highlighted-button"
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar)}
          >
            {this.props.current_bar + 1}
          </button>
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar + 1)}
          >
            {this.props.current_bar + 2}
          </button>
        </div>
        <div>
          Move:
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar - 16)}
          >
            -16 bars
          </button>
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar - 4)}
          >
            -4 bars
          </button>
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar + 4)}
          >
            +4 bars
          </button>
          <button
            onClick={(evt) => this.props.onGoToBar(this.props.current_bar + 16)}
          >
            +16 bars
          </button>
        </div>
      </div>
    );
  }

  updateBeatNumber(evt) {
    this.setState({
      beat_number: parseInt(evt.target.value) - 1,
    });
  }
}
